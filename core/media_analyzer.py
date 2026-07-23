"""Media analysis helpers for import, library filters and performance advice."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtGui import QImageReader

from core.video_optimizer import VIDEO_SUFFIXES, VideoOptimizer


MEDIA_EXTENSIONS = {
    "image": {".bmp", ".jpeg", ".jpg", ".png", ".webp"},
    "gif": {".gif"},
    "video": {".mp4", ".webm", *VIDEO_SUFFIXES},
}


@dataclass(frozen=True)
class MediaAnalysis:
    kind: str
    width: int = 0
    height: int = 0
    duration_seconds: float = 0.0
    fps: float = 0.0
    codec: str = ""
    size_mb: float = 0.0
    resource_class: str = "leve"
    tags: tuple[str, ...] = ()
    message: str = ""

    @property
    def resolution_label(self) -> str:
        return f"{self.width}x{self.height}" if self.width and self.height else "resolucao desconhecida"

    @property
    def user_summary(self) -> str:
        parts = [self.kind, self.resource_class, self.resolution_label, f"{self.size_mb:.1f} MB"]
        if self.fps:
            parts.append(f"{self.fps:.0f} FPS")
        if self.codec:
            parts.append(self.codec)
        return " | ".join(parts)


def analyze_media(path: Path) -> MediaAnalysis:
    kind = _kind_for_path(path)
    size_mb = _safe_size_mb(path)
    if kind in {"image", "gif"}:
        width, height = _image_dimensions(path)
        resource_class = _resource_class(kind, width, height, 0.0, size_mb)
        return MediaAnalysis(
            kind=kind or "arquivo",
            width=width,
            height=height,
            size_mb=size_mb,
            resource_class=resource_class,
            tags=_tags_for(kind or "", width, height, 0.0, size_mb, ""),
            message=_message_for(resource_class, kind or "", 0.0),
        )
    if kind == "video":
        width, height, fps, duration, codec = _video_metadata(path)
        resource_class = _resource_class(kind, width, height, fps, size_mb)
        return MediaAnalysis(
            kind=kind,
            width=width,
            height=height,
            fps=fps,
            duration_seconds=duration,
            codec=codec,
            size_mb=size_mb,
            resource_class=resource_class,
            tags=_tags_for(kind, width, height, fps, size_mb, codec),
            message=_message_for(resource_class, kind, fps),
        )
    return MediaAnalysis(kind=kind or "arquivo", size_mb=size_mb, message="Arquivo nao reconhecido.")


def _kind_for_path(path: Path) -> str | None:
    suffix = path.suffix.lower()
    for kind, extensions in MEDIA_EXTENSIONS.items():
        if suffix in extensions:
            return kind
    if suffix in VIDEO_SUFFIXES:
        return "video"
    return None


def _safe_size_mb(path: Path) -> float:
    try:
        return path.stat().st_size / 1024 / 1024
    except OSError:
        return 0.0


def _image_dimensions(path: Path) -> tuple[int, int]:
    reader = QImageReader(str(path))
    size = reader.size()
    if size.isValid():
        return size.width(), size.height()
    return 0, 0


def _video_metadata(path: Path) -> tuple[int, int, float, float, str]:
    ffmpeg = VideoOptimizer.ffmpeg_path()
    if not ffmpeg:
        return 0, 0, 0.0, 0.0, ""
    command = [str(ffmpeg), "-hide_banner", "-i", str(path)]
    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0, 0, 0.0, 0.0, ""
    text = completed.stderr or ""
    duration = _parse_duration(text)
    width = height = 0
    fps = 0.0
    codec = ""
    for line in text.splitlines():
        if " Video: " not in line:
            continue
        codec_match = re.search(r"Video:\s*([^,\s]+)", line)
        size_match = re.search(r"(\d{3,5})x(\d{3,5})", line)
        fps_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*fps", line)
        if codec_match:
            codec = codec_match.group(1)
        if size_match:
            width = int(size_match.group(1))
            height = int(size_match.group(2))
        if fps_match:
            fps = float(fps_match.group(1))
        break
    return width, height, fps, duration, codec


def _parse_duration(text: str) -> float:
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    if not match:
        return 0.0
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _resource_class(kind: str | None, width: int, height: int, fps: float, size_mb: float) -> str:
    pixels = width * height
    if kind == "video":
        if size_mb >= 250 or pixels >= 3840 * 2160 or fps >= 55:
            return "pesado"
        if size_mb >= 90 or pixels >= 1920 * 1080 or fps >= 31:
            return "medio"
        return "leve"
    if kind == "gif":
        if size_mb >= 80 or pixels >= 1920 * 1080:
            return "pesado"
        if size_mb >= 25 or pixels >= 1280 * 720:
            return "medio"
        return "leve"
    if pixels >= 3840 * 2160 or size_mb >= 25:
        return "pesado"
    if pixels >= 1920 * 1080 or size_mb >= 8:
        return "medio"
    return "leve"


def _tags_for(kind: str, width: int, height: int, fps: float, size_mb: float, codec: str) -> tuple[str, ...]:
    tags = {kind} if kind else set()
    resource = _resource_class(kind, width, height, fps, size_mb)
    tags.add(resource)
    if width >= 3840 or height >= 2160:
        tags.add("4k")
    elif width >= 1920 or height >= 1080:
        tags.add("full-hd")
    if fps >= 55:
        tags.add("60fps")
    if codec:
        tags.add(codec.lower())
    return tuple(sorted(tags))


def _message_for(resource_class: str, kind: str, fps: float) -> str:
    if resource_class == "pesado" and kind == "video":
        return "Video pesado detectado. O Movaura pode criar uma copia otimizada para manter fluidez."
    if resource_class == "medio" and kind == "video":
        return "Video medio detectado. Use o perfil Recomendado ou Leve se notar consumo alto."
    if kind == "gif" and resource_class != "leve":
        return "GIF grande detectado. Converter para video otimizado costuma consumir menos CPU."
    if fps >= 55:
        return "Video em alta taxa de quadros detectado. O modo adaptativo pode limitar FPS automaticamente."
    return "Midia pronta para uso."
