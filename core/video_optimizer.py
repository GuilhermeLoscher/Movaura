"""Video optimization cache for Movaura. Desenvolvido por Guilherme Loscher (GL)."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from core.runtime_paths import app_root, data_root, resource_root


VIDEO_SUFFIXES = {".mp4", ".m4v", ".mov", ".webm", ".mkv", ".avi"}


@dataclass(frozen=True)
class VideoOptimizationResult:
    path: str
    optimized: bool
    message: str


@dataclass(frozen=True)
class VideoOptimizationProfile:
    width: int
    height: int
    fps: int
    bitrate: str
    maxrate: str
    bufsize: str
    preset: str


class VideoOptimizer:
    """Creates playback-friendly copies of heavy videos before live rendering."""

    def __init__(self) -> None:
        self.cache_dir = data_root() / "optimized_videos"

    def optimize(
        self,
        media_path: str,
        performance_profile: str,
        fps: int,
        multi_monitor_mode: str = "repeat",
    ) -> VideoOptimizationResult:
        source = Path(media_path).expanduser()
        try:
            is_video = source.is_file() and source.suffix.lower() in VIDEO_SUFFIXES
        except OSError as exc:
            return VideoOptimizationResult(media_path, False, f"vídeo inacessível: {exc}")
        if not is_video:
            return VideoOptimizationResult(media_path, False, "arquivo não é um vídeo otimizável")

        ffmpeg = self.ffmpeg_path()
        if not ffmpeg:
            return VideoOptimizationResult(
                media_path,
                False,
                "FFmpeg não encontrado; usando vídeo original",
            )

        profile = self._profile(performance_profile, fps, multi_monitor_mode)
        key = self._cache_key(source, profile)
        destination = self.cache_dir / f"{key}_{profile.width}x{profile.height}_{profile.fps}fps.mp4"
        if destination.is_file() and destination.stat().st_size > 1024 * 1024:
            return VideoOptimizationResult(
                str(destination),
                True,
                f"vídeo otimizado em cache: {destination.name}",
            )

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp.mp4")
        if temporary.exists():
            temporary.unlink()

        command = [
            str(ffmpeg),
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-an",
            "-vf",
            (
                f"scale=w='min({profile.width},iw)':h='min({profile.height},ih)':"
                "force_original_aspect_ratio=decrease:force_divisible_by=2,"
                f"fps={profile.fps}"
            ),
            "-c:v",
            "libopenh264",
            "-pix_fmt",
            "yuv420p",
            "-b:v",
            profile.bitrate,
            "-maxrate",
            profile.maxrate,
            "-bufsize",
            profile.bufsize,
            "-movflags",
            "+faststart",
            str(temporary),
        ]
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        try:
            completed = subprocess.run(
                command,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creationflags,
            )
        except OSError as exc:
            return VideoOptimizationResult(media_path, False, f"falha ao otimizar vídeo: {exc}")

        if completed.returncode != 0 or not temporary.exists():
            detail = (completed.stderr or "").strip().splitlines()[-1:] or ["erro desconhecido"]
            if temporary.exists():
                temporary.unlink()
            return VideoOptimizationResult(
                media_path,
                False,
                f"otimização de vídeo falhou: {detail[0]}",
            )

        temporary.replace(destination)
        self._prune_cache(max_items=24)
        return VideoOptimizationResult(
            str(destination),
            True,
            f"vídeo otimizado para baixo consumo: {destination.name}",
        )

    @staticmethod
    def ffmpeg_path() -> Path | None:
        candidates = [
            resource_root() / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
            app_root() / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
            Path(sys.executable).resolve().parent / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
            resource_root() / "tools" / "ffmpeg" / "ffmpeg.exe",
            app_root() / "tools" / "ffmpeg" / "ffmpeg.exe",
            Path(sys.executable).resolve().parent / "tools" / "ffmpeg" / "ffmpeg.exe",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        found = shutil.which("ffmpeg")
        return Path(found) if found else None

    @staticmethod
    def _profile(
        performance_profile: str,
        fps: int,
        multi_monitor_mode: str,
    ) -> VideoOptimizationProfile:
        requested_fps = max(1, min(int(fps), 60))
        if performance_profile == "quality":
            return VideoOptimizationProfile(1920, 1080, min(requested_fps, 30), "5500k", "6500k", "12000k", "veryfast")
        if performance_profile == "balanced":
            return VideoOptimizationProfile(1600, 900, min(requested_fps, 30), "3500k", "4200k", "8000k", "veryfast")
        if performance_profile == "adaptive" and multi_monitor_mode == "span":
            return VideoOptimizationProfile(1920, 1080, min(requested_fps, 24), "4500k", "5400k", "10000k", "veryfast")
        return VideoOptimizationProfile(1280, 720, min(requested_fps, 15), "2200k", "2800k", "5600k", "veryfast")

    @staticmethod
    def _cache_key(source: Path, profile: VideoOptimizationProfile) -> str:
        stat = source.stat()
        payload = (
            str(source.resolve()).lower(),
            str(stat.st_size),
            str(int(stat.st_mtime)),
            str(profile),
        )
        return hashlib.sha256("|".join(payload).encode("utf-8")).hexdigest()[:20]

    def _prune_cache(self, max_items: int) -> None:
        videos = sorted(
            self.cache_dir.glob("*.mp4"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for stale in videos[max_items:]:
            try:
                stale.unlink()
            except OSError:
                pass
