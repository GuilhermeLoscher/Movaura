from __future__ import annotations

from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from cache.wallpaper_cache import WallpaperCache


ProgressCallback = Callable[[int, str], None]
CancelCallback = Callable[[], bool]


class DownloadError(RuntimeError):
    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)
        self.user_message = user_message


class DownloadManager:
    def __init__(self, cache: WallpaperCache | None = None) -> None:
        self.cache = cache or WallpaperCache()

    def download(
        self,
        url: str,
        progress: ProgressCallback | None = None,
        should_cancel: CancelCallback | None = None,
    ) -> Path:
        if not url.lower().startswith("https://"):
            raise DownloadError("Por seguranca, o download precisa usar HTTPS.")
        target = self.cache.cached_file_for_url(url)
        if target.is_file() and target.stat().st_size > 0:
            if progress:
                progress(100, "Arquivo encontrado no cache.")
            return target
        return self._download_to(url, target, progress, should_cancel)

    def download_thumbnail(self, url: str) -> Path | None:
        if not url.lower().startswith("https://"):
            return None
        target = self.cache.cached_thumbnail_for_url(url)
        if target.is_file() and target.stat().st_size > 0:
            return target
        try:
            return self._download_to(url, target, None, None, timeout=8)
        except DownloadError:
            return None

    def _download_to(
        self,
        url: str,
        target: Path,
        progress: ProgressCallback | None,
        should_cancel: CancelCallback | None,
        timeout: int = 40,
    ) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(f"{target.suffix}.part")
        request = Request(url, headers={"User-Agent": "Movaura/0.9"})
        try:
            with urlopen(request, timeout=timeout) as response:
                total = int(response.headers.get("Content-Length", "0") or 0)
                done = 0
                with temporary.open("wb") as output:
                    while True:
                        if should_cancel and should_cancel():
                            temporary.unlink(missing_ok=True)
                            raise DownloadError("Download cancelado.")
                        chunk = response.read(128 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
                        done += len(chunk)
                        if progress and total:
                            progress(min(99, int(done * 100 / total)), "Baixando wallpaper...")
        except HTTPError as exc:
            temporary.unlink(missing_ok=True)
            raise DownloadError(f"O servidor recusou o download ({exc.code}).") from exc
        except (URLError, TimeoutError, OSError) as exc:
            temporary.unlink(missing_ok=True)
            raise DownloadError("Falha ao baixar o wallpaper. Verifique a internet e tente novamente.") from exc
        temporary.replace(target)
        if progress:
            progress(100, "Download concluido.")
        return target

