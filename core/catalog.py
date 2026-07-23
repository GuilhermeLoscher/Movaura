from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from core.runtime_paths import data_root
from core.runtime_paths import resource_root
from core.wallpaper_library import WallpaperLibrary


@dataclass(frozen=True)
class CatalogItem:
    name: str
    kind: str
    download_url: str
    sha256: str = ""
    description: str = ""


class OnlineCatalog:
    def fetch(self, manifest_url: str) -> list[CatalogItem]:
        manifest_url = manifest_url.strip()
        if not manifest_url:
            local_manifest = resource_root() / "data" / "catalog.json"
            if not local_manifest.is_file():
                raise ValueError("Informe a URL do catálogo ou inclua data/catalog.json.")
            data = json.loads(local_manifest.read_text(encoding="utf-8"))
        elif urlparse(manifest_url).scheme in {"http", "https"}:
            with urlopen(manifest_url, timeout=6) as response:
                data = json.loads(response.read().decode("utf-8"))
        elif Path(manifest_url).expanduser().is_file():
            data = json.loads(Path(manifest_url).expanduser().read_text(encoding="utf-8"))
        else:
            raise ValueError("Catálogo inválido. Use uma URL http/https ou um arquivo JSON local.")
        entries = data.get("wallpapers", []) if isinstance(data, dict) else []
        return [
            CatalogItem(
                name=str(entry.get("name", "Wallpaper")),
                kind=str(entry.get("kind", "")),
                download_url=str(entry.get("download_url", "")),
                sha256=str(entry.get("sha256", "")).lower(),
                description=str(entry.get("description", "")),
            )
            for entry in entries
            if isinstance(entry, dict) and entry.get("download_url")
        ]

    def download(self, item: CatalogItem) -> Path:
        source = self._resolve_source(item.download_url)
        suffix = Path(urlparse(item.download_url).path).suffix.lower() or source.suffix.lower()
        filename = self._safe_filename(item.name) + suffix
        staging = data_root() / "downloads"
        staging.mkdir(parents=True, exist_ok=True)
        target = staging / filename
        if source.is_file():
            target.write_bytes(source.read_bytes())
        else:
            with urlopen(item.download_url, timeout=20) as response:
                target.write_bytes(response.read())
        if item.sha256 and hashlib.sha256(target.read_bytes()).hexdigest().lower() != item.sha256:
            target.unlink(missing_ok=True)
            raise ValueError("O arquivo baixado não passou na verificação SHA-256.")
        if not WallpaperLibrary.kind_for_path(target):
            target.unlink(missing_ok=True)
            raise ValueError("O catálogo retornou um formato incompatível.")
        return target

    @staticmethod
    def _safe_filename(name: str) -> str:
        safe = "".join(char.lower() if char.isalnum() else "-" for char in name).strip("-")
        return safe or "wallpaper"

    @staticmethod
    def _resolve_source(download_url: str) -> Path:
        parsed = urlparse(download_url)
        if parsed.scheme == "file":
            return Path(parsed.path)
        if parsed.scheme:
            return Path("")
        path = Path(download_url)
        if path.is_absolute():
            return path
        return resource_root() / path
