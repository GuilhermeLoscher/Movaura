from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtGui import QIcon, QImageReader, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink

from core.runtime_paths import data_root


class ThumbnailCache(QObject):
    ready = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.root = data_root() / "thumbnails"
        try:
            self.root.mkdir(parents=True, exist_ok=True)
        except OSError:
            self.root = Path(tempfile.gettempdir()) / "Movaura" / "thumbnails"
            self.root.mkdir(parents=True, exist_ok=True)
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

    def request_video(self, source: Path) -> None:
        thumbnail = self.cached_path(source)
        if thumbnail.is_file() or source in self.queue or source == self.current:
            return
        self.queue.append(source)
        self._start_next()

    def metadata(self, source: Path) -> dict[str, object]:
        try:
            return json.loads(self.metadata_path(source).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

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
        image.scaled(380, 216).save(str(target), "JPG", 86)
        self.metadata_path(self.current).write_text(
            json.dumps(
                {
                    "width": image.width(),
                    "height": image.height(),
                    "duration_ms": self.player.duration(),
                },
                indent=2,
            ),
            encoding="utf-8",
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
    return hashlib.sha256(str(source.resolve()).lower().encode("utf-8")).hexdigest()[:24]
