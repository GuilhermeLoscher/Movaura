from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname, urlopen

from core.runtime_paths import data_root
from core.runtime_paths import resource_root
from core.wallpaper_library import WallpaperLibrary


@dataclass(frozen=True)
class CatalogSource:
    kind: str
    value: str | Path


@dataclass(frozen=True)
class CatalogItem:
    name: str
    kind: str
    download_url: str
    sha256: str = ""
    description: str = ""
    catalog_base: Path | None = None


class OnlineCatalog:
    def fetch(self, manifest_url: str) -> list[CatalogItem]:
        manifest_url = manifest_url.strip()
        catalog_base: Path | None = None
        if not manifest_url:
            local_manifest = resource_root() / "data" / "catalog.json"
            if not local_manifest.is_file():
                raise ValueError("Informe a URL do catalogo ou inclua data/catalog.json.")
            catalog_base = local_manifest.parent
            data = json.loads(local_manifest.read_text(encoding="utf-8"))
        elif urlparse(manifest_url).scheme in {"http", "https"}:
            with urlopen(manifest_url, timeout=6) as response:
                data = json.loads(response.read().decode("utf-8"))
        elif Path(manifest_url).expanduser().is_file():
            local_manifest = Path(manifest_url).expanduser()
            catalog_base = local_manifest.parent
            data = json.loads(local_manifest.read_text(encoding="utf-8"))
        else:
            raise ValueError("Catalogo invalido. Use uma URL http/https ou um arquivo JSON local.")
        entries = data.get("wallpapers", []) if isinstance(data, dict) else []
        return [
            CatalogItem(
                name=str(entry.get("name", "Wallpaper")),
                kind=str(entry.get("kind", "")),
                download_url=str(entry.get("download_url", "")),
                sha256=str(entry.get("sha256", "")).lower(),
                description=str(entry.get("description", "")),
                catalog_base=catalog_base,
            )
            for entry in entries
            if isinstance(entry, dict) and entry.get("download_url")
        ]

    def download(self, item: CatalogItem) -> Path:
        source = self.resolve_source(item.download_url, item.catalog_base)
        if source.kind == "url":
            suffix = Path(urlparse(str(source.value)).path).suffix.lower()
        else:
            suffix = Path(source.value).suffix.lower()
        filename = self._safe_filename(item.name) + suffix
        staging = data_root() / "downloads"
        staging.mkdir(parents=True, exist_ok=True)
        target = staging / filename
        if source.kind == "file":
            target.write_bytes(Path(source.value).read_bytes())
        else:
            with urlopen(str(source.value), timeout=20) as response:
                target.write_bytes(response.read())
        if item.sha256 and hashlib.sha256(target.read_bytes()).hexdigest().lower() != item.sha256:
            target.unlink(missing_ok=True)
            raise ValueError("O arquivo baixado nao passou na verificacao SHA-256.")
        if not WallpaperLibrary.kind_for_path(target):
            target.unlink(missing_ok=True)
            raise ValueError("O catalogo retornou um formato incompativel.")
        return target

    @staticmethod
    def _safe_filename(name: str) -> str:
        safe = "".join(char.lower() if char.isalnum() else "-" for char in name).strip("-")
        return safe or "wallpaper"

    @staticmethod
    def resolve_source(
        download_url: str,
        catalog_base: Path | None = None,
        package_root: Path | None = None,
    ) -> CatalogSource:
        download_url = download_url.strip()
        if not download_url:
            raise ValueError("Fonte do catalogo vazia.")
        parsed = urlparse(download_url)
        if parsed.scheme in {"http", "https"}:
            if not parsed.netloc:
                raise ValueError("URL do catalogo invalida.")
            return CatalogSource("url", download_url)
        if parsed.scheme == "file":
            path = Path(url2pathname(unquote(parsed.path))).expanduser()
            return CatalogSource("file", OnlineCatalog._validated_existing_file(path))
        if parsed.scheme:
            raise ValueError(f"Esquema de catalogo nao suportado: {parsed.scheme}.")
        path = Path(download_url)
        if path.is_absolute():
            return CatalogSource("file", OnlineCatalog._validated_existing_file(path))

        root = package_root or resource_root()
        candidates = []
        if catalog_base is not None:
            candidates.append(catalog_base / path)
        candidates.append(root / path)
        candidates.append(root / "data" / path)

        allowed_roots = [root]
        if catalog_base is not None:
            allowed_roots.append(catalog_base)
        for candidate in candidates:
            resolved = candidate.resolve(strict=False)
            if not OnlineCatalog._is_inside_any(resolved, allowed_roots):
                continue
            if resolved.is_file():
                return CatalogSource("file", resolved)
        raise FileNotFoundError(
            "Arquivo do catalogo nao encontrado no pacote do Movaura: "
            f"{download_url}"
        )

    @staticmethod
    def _validated_existing_file(path: Path) -> Path:
        resolved = path.resolve(strict=False)
        if not resolved.is_file():
            raise FileNotFoundError(f"Arquivo do catalogo nao encontrado: {path}")
        return resolved

    @staticmethod
    def _is_inside_any(path: Path, roots: list[Path]) -> bool:
        for root in roots:
            try:
                path.relative_to(root.resolve(strict=False))
                return True
            except ValueError:
                continue
        return False
