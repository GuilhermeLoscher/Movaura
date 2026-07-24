from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path
from threading import Lock, Thread
from time import monotonic

from PySide6.QtCore import QObject, QTimer, QUrl, Qt, Signal
from PySide6.QtGui import QIcon, QImageReader, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink

from core.json_store import write_json_atomic
from core.runtime_paths import data_root

LOGGER = logging.getLogger(__name__)

THUMBNAIL_ALGORITHM_VERSION = "thumb-v2"
THUMBNAIL_WIDTH = 380
THUMBNAIL_HEIGHT = 216
THUMBNAIL_QUALITY = 86
DEFAULT_CACHE_LIMIT_BYTES = 512 * 1024 * 1024
MAX_CACHE_FILES = 1500


class ThumbnailCache(QObject):
    ready = Signal(str)
    failed = Signal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.root = data_root() / "thumbnails"
        try:
            self.root.mkdir(parents=True, exist_ok=True)
        except OSError:
            self.root = Path(tempfile.gettempdir()) / "Movaura" / "thumbnails"
            self.root.mkdir(parents=True, exist_ok=True)
        LOGGER.info("Thumbnail cache location: %s", self.root)
        self._lock = Lock()
        self._image_queue: list[Path] = []
        self._image_pending: set[str] = set()
        self._image_current: Path | None = None
        self._closed = False
        self._prune_scheduled = False
        self.queue: list[Path] = []
        self.current: Path | None = None
        self.player = QMediaPlayer(self)
        self.sink = QVideoSink(self)
        self.player.setVideoSink(self.sink)
        self.sink.videoFrameChanged.connect(self._frame_ready)
        self.player.durationChanged.connect(self._duration_changed)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._finish_current)

    def cached_path(self, source: Path) -> Path:
        digest = thumbnail_digest(source)
        return self.root / f"{digest}.jpg"

    def metadata_path(self, source: Path) -> Path:
        return self.cached_path(source).with_suffix(".json")

    def cache_hit(self, source: Path) -> bool:
        thumbnail = self.cached_path(source)
        if not thumbnail.is_file():
            return False
        metadata = self.metadata(source)
        if metadata.get("version") != THUMBNAIL_ALGORITHM_VERSION:
            return False
        try:
            if thumbnail.stat().st_size <= 0:
                return False
            os.utime(thumbnail, None)
            sidecar = self.metadata_path(source)
            if sidecar.is_file():
                os.utime(sidecar, None)
        except OSError:
            return False
        return True

    def request_image(self, source: Path) -> None:
        if self._closed or self.cache_hit(source):
            return
        key = thumbnail_digest(source)
        with self._lock:
            if key in self._image_pending:
                return
            self._image_pending.add(key)
            self._image_queue.append(source)
        self._start_next_image()

    def request_video(self, source: Path) -> None:
        if self._closed or self.cache_hit(source):
            return
        if source in self.queue or source == self.current:
            return
        LOGGER.debug("Thumbnail cache miss for video: %s", source)
        self.queue.append(source)
        self._start_next()

    def metadata(self, source: Path) -> dict[str, object]:
        try:
            return json.loads(self.metadata_path(source).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def cancel_pending(self) -> None:
        self._closed = True
        with self._lock:
            self._image_queue.clear()
            self._image_pending.clear()
        self.queue.clear()
        self.timer.stop()
        self.player.stop()
        self.player.setSource(QUrl())
        self.current = None

    def prune(self, max_bytes: int = DEFAULT_CACHE_LIMIT_BYTES, max_files: int = MAX_CACHE_FILES) -> None:
        if self._prune_scheduled:
            return
        self._prune_scheduled = True

        def run() -> None:
            start = monotonic()
            removed = 0
            initial_size = 0
            final_size = 0
            try:
                files = [path for path in self.root.glob("*") if path.is_file() and self._is_inside_cache(path)]
                candidates: list[tuple[float, int, Path]] = []
                for path in files:
                    try:
                        stat = path.stat()
                    except OSError:
                        continue
                    initial_size += stat.st_size
                    candidates.append((stat.st_atime, stat.st_size, path))
                candidates.sort(key=lambda item: item[0])
                current_size = initial_size
                while candidates and (current_size > max_bytes or len(candidates) > max_files):
                    _, size, path = candidates.pop(0)
                    try:
                        path.unlink()
                        current_size -= size
                        removed += 1
                    except OSError:
                        LOGGER.debug("Could not prune thumbnail cache entry: %s", path)
                final_size = max(0, current_size)
            finally:
                self._prune_scheduled = False
                LOGGER.info(
                    "Thumbnail cache prune: initial=%s final=%s removed=%s duration=%.3fs",
                    initial_size,
                    final_size,
                    removed,
                    monotonic() - start,
                )

        Thread(target=run, daemon=True).start()

    def _start_next(self) -> None:
        if self.current or not self.queue:
            return
        self.current = self.queue.pop(0)
        self.player.setSource(QUrl.fromLocalFile(str(self.current)))
        self.player.play()
        self.timer.start(3500)

    def _duration_changed(self, duration: int) -> None:
        if duration > 0:
            self.player.setPosition(min(1000, duration // 3))

    def _frame_ready(self, frame) -> None:
        if not self.current or not frame.isValid():
            return
        image = frame.toImage()
        if image.isNull():
            return
        target = self.cached_path(self.current)
        self._save_thumbnail_image(
            image,
            target,
            self.metadata_path(self.current),
            {
                "kind": "video",
                "width": image.width(),
                "height": image.height(),
                "duration_ms": self.player.duration(),
            },
        )
        self._finish_current()

    def _finish_current(self) -> None:
        if not self.current:
            return
        completed = self.current
        self.timer.stop()
        self.player.stop()
        self.player.setSource(QUrl())
        self.current = None
        self.ready.emit(str(completed))
        QTimer.singleShot(0, self._start_next)

    def _start_next_image(self) -> None:
        if self._closed:
            return
        with self._lock:
            if self._image_current or not self._image_queue:
                return
            source = self._image_queue.pop(0)
            self._image_current = source

        Thread(target=self._generate_image_thumbnail, args=(source,), daemon=True).start()

    def _generate_image_thumbnail(self, source: Path) -> None:
        error = ""
        try:
            target = self.cached_path(source)
            metadata_path = self.metadata_path(source)
            reader = QImageReader(str(source))
            reader.setAutoTransform(True)
            image = reader.read()
            if image.isNull():
                error = reader.errorString() or "Imagem invalida."
            else:
                self._save_thumbnail_image(
                    image,
                    target,
                    metadata_path,
                    {
                        "kind": "image",
                        "width": image.width(),
                        "height": image.height(),
                    },
                )
        except OSError as exc:
            error = str(exc)
        finally:
            key = thumbnail_digest(source)
            with self._lock:
                self._image_pending.discard(key)
                if self._image_current == source:
                    self._image_current = None
            if error:
                LOGGER.warning("Thumbnail image generation failed for %s: %s", source, error)
                self.failed.emit(str(source), error)
            elif not self._closed:
                self.ready.emit(str(source))
            if not self._closed:
                self._start_next_image()

    def _save_thumbnail_image(self, image, target: Path, metadata_path: Path, metadata: dict[str, object]) -> None:
        scaled = image.scaled(
            THUMBNAIL_WIDTH,
            THUMBNAIL_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        temporary = target.with_suffix(".tmp.jpg")
        if not scaled.save(str(temporary), "JPG", THUMBNAIL_QUALITY):
            raise OSError(f"Nao foi possivel salvar miniatura em {target}")
        temporary.replace(target)
        payload = {
            "version": THUMBNAIL_ALGORITHM_VERSION,
            "thumb_width": THUMBNAIL_WIDTH,
            "thumb_height": THUMBNAIL_HEIGHT,
            **metadata,
        }
        write_json_atomic(metadata_path, payload)

    def _is_inside_cache(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.root.resolve())
            return True
        except (OSError, ValueError):
            return False


def image_dimensions(path: Path) -> tuple[int, int] | None:
    reader = QImageReader(str(path))
    size = reader.size()
    if size.isValid():
        return size.width(), size.height()
    return None


def scaled_icon(path: Path, width: int = 190, height: int = 108) -> QIcon | None:
    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return None
    return QIcon(pixmap.scaled(width, height))


def thumbnail_digest(source: Path) -> str:
    try:
        resolved = str(source.resolve()).lower()
    except OSError:
        resolved = str(source.absolute()).lower()
    try:
        stat = source.stat()
        size = stat.st_size
        mtime_ns = stat.st_mtime_ns
    except OSError:
        size = 0
        mtime_ns = 0
    suffix = source.suffix.lower()
    payload = "|".join(
        (
            THUMBNAIL_ALGORITHM_VERSION,
            resolved,
            suffix,
            str(size),
            str(mtime_ns),
            str(THUMBNAIL_WIDTH),
            str(THUMBNAIL_HEIGHT),
        )
    )
    return hashlib.sha256(payload.encode("utf-8", errors="surrogatepass")).hexdigest()[:32]
