from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from core.json_store import read_json_object, write_json_atomic
from core.runtime_paths import data_root
from models.wallpaper_result import WallpaperResult, WallpaperSearchQuery


class WallpaperCache:
    def __init__(self, root: Path | None = None, ttl_seconds: int = 1800) -> None:
        self.root = root or data_root() / "online_cache"
        self.search_root = self.root / "search"
        self.file_root = self.root / "files"
        self.thumbnail_root = self.root / "thumbnails"
        self.ttl_seconds = ttl_seconds

    def search_key(self, provider_id: str, query: WallpaperSearchQuery) -> str:
        payload = json.dumps(
            {
                "provider": provider_id,
                "text": query.normalized_text,
                "resolution": query.resolution,
                "orientation": query.orientation,
                "color": query.color,
                "page": query.page,
                "per_page": query.per_page,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def read_search(self, provider_id: str, query: WallpaperSearchQuery) -> list[WallpaperResult] | None:
        path = self.search_root / f"{self.search_key(provider_id, query)}.json"
        data = read_json_object(path)
        if not data:
            return None
        timestamp = float(data.get("timestamp", 0) or 0)
        if time.time() - timestamp > self.ttl_seconds:
            return None
        entries = data.get("results", [])
        if not isinstance(entries, list):
            return None
        return [WallpaperResult(**entry) for entry in entries if isinstance(entry, dict)]

    def write_search(self, provider_id: str, query: WallpaperSearchQuery, results: Iterable[WallpaperResult]) -> None:
        path = self.search_root / f"{self.search_key(provider_id, query)}.json"
        write_json_atomic(path, {"timestamp": time.time(), "results": [asdict(result) for result in results]})

    def cached_file_for_url(self, url: str) -> Path:
        suffix = self._suffix(url, ".jpg")
        return self.file_root / f"{self.url_key(url)}{suffix}"

    def cached_thumbnail_for_url(self, url: str) -> Path:
        suffix = self._suffix(url, ".jpg")
        return self.thumbnail_root / f"{self.url_key(url)}{suffix}"

    @staticmethod
    def url_key(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    @staticmethod
    def _suffix(url: str, fallback: str) -> str:
        name = url.split("?", 1)[0].rsplit("/", 1)[-1]
        suffix = Path(name).suffix.lower()
        return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else fallback

