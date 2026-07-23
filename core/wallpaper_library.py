from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from core.json_store import write_json_atomic
from core.media_analyzer import MEDIA_EXTENSIONS, analyze_media
from core.runtime_paths import app_root, data_root


SUPPORTED_EXTENSIONS = MEDIA_EXTENSIONS


@dataclass(frozen=True)
class WallpaperItem:
    kind: str
    path: Path
    name: str
    included: bool
    favorite: bool
    recent: bool = False
    tags: tuple[str, ...] = ()
    collection: str = ""
    resource_class: str = "leve"


class WallpaperLibrary:
    def __init__(self) -> None:
        self.included_root = app_root() / "wallpapers"
        self.personal_root = data_root() / "wallpapers"
        self.metadata_path = data_root() / "library.json"
        self.personal_root.mkdir(parents=True, exist_ok=True)
        self._metadata = self._load_metadata()

    def items(self) -> list[WallpaperItem]:
        items: list[WallpaperItem] = []
        items.extend(self._scan_root(self.included_root, included=True))
        items.extend(self._scan_root(self.personal_root, included=False))
        return sorted(items, key=lambda item: (item.kind, item.name.lower()))

    def import_files(self, paths: list[Path]) -> list[WallpaperItem]:
        imported: list[WallpaperItem] = []
        for source in paths:
            kind = self.kind_for_path(source)
            if not kind or not source.is_file():
                continue
            destination_dir = self.personal_root / self.folder_for_kind(kind)
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination = self._available_destination(destination_dir, source.name)
            shutil.copy2(source, destination)
            analysis = analyze_media(destination)
            imported.append(
                WallpaperItem(
                    kind=kind,
                    path=destination,
                    name=destination.stem.replace("-", " ").title(),
                    included=False,
                    favorite=False,
                    recent=False,
                    tags=analysis.tags,
                    collection="Importados",
                    resource_class=analysis.resource_class,
                )
            )
            self.update_details(imported[-1], list(analysis.tags), "Importados", analysis.resource_class)
        return imported

    def import_folder(self, folder: Path) -> list[WallpaperItem]:
        if not folder.is_dir():
            return []
        return self.import_files(
            [path for path in folder.rglob("*") if path.is_file() and self.kind_for_path(path)]
        )

    def remove_personal(self, item: WallpaperItem) -> bool:
        if item.included or not item.path.is_file():
            return False
        try:
            item.path.unlink()
        except OSError:
            return False
        key = self._key(item.path)
        self._metadata["favorites"] = [
            favorite for favorite in self._metadata["favorites"] if favorite != key
        ]
        self._metadata["recent"] = [
            recent for recent in self._metadata["recent"] if recent != key
        ]
        self._metadata.setdefault("details", {}).pop(key, None)
        self._save_metadata()
        return True

    def toggle_favorite(self, item: WallpaperItem) -> bool:
        key = self._key(item.path)
        favorites = set(self._metadata["favorites"])
        if key in favorites:
            favorites.remove(key)
            favorite = False
        else:
            favorites.add(key)
            favorite = True
        self._metadata["favorites"] = sorted(favorites)
        self._save_metadata()
        return favorite

    def mark_recent(self, item: WallpaperItem) -> None:
        key = self._key(item.path)
        recent = [current for current in self._metadata["recent"] if current != key]
        self._metadata["recent"] = [key, *recent][:20]
        self._save_metadata()

    def recent_rank(self, item: WallpaperItem) -> int:
        key = self._key(item.path)
        try:
            return self._metadata["recent"].index(key)
        except ValueError:
            return 10_000

    def update_details(
        self,
        item: WallpaperItem,
        tags: list[str],
        collection: str,
        resource_class: str | None = None,
    ) -> None:
        key = self._key(item.path)
        clean_tags = sorted({tag.strip()[:40] for tag in tags if tag.strip()})
        clean_resource = (resource_class or item.resource_class or "leve").strip().lower()
        if clean_resource not in {"leve", "medio", "pesado"}:
            clean_resource = "leve"
        self._metadata.setdefault("details", {})[key] = {
            "tags": clean_tags[:20],
            "collection": collection.strip()[:80],
            "resource_class": clean_resource,
        }
        self._save_metadata()

    def collections(self) -> list[str]:
        return sorted(
            {
                str(details.get("collection", ""))
                for details in self._metadata.get("details", {}).values()
                if isinstance(details, dict) and details.get("collection")
            }
        )

    def missing_files(self) -> list[str]:
        return [key for key in self._metadata.get("details", {}) if not Path(key).is_file()]

    def locate_missing(self, missing_path: str, replacement: Path) -> bool:
        if not replacement.is_file() or not self.kind_for_path(replacement):
            return False
        details_store = self._metadata.setdefault("details", {})
        details = details_store.pop(missing_path, {})
        details_store[self._key(replacement)] = details
        self._save_metadata()
        return True

    def stats(self) -> dict[str, int]:
        items = self.items()
        return {
            "total": len(items),
            "images": sum(item.kind == "image" for item in items),
            "gifs": sum(item.kind == "gif" for item in items),
            "videos": sum(item.kind == "video" for item in items),
            "favorites": sum(item.favorite for item in items),
            "personal": sum(not item.included for item in items),
        }

    @staticmethod
    def kind_for_path(path: Path) -> str | None:
        suffix = path.suffix.lower()
        for kind, extensions in SUPPORTED_EXTENSIONS.items():
            if suffix in extensions:
                return kind
        return None

    @staticmethod
    def folder_for_kind(kind: str) -> str:
        return {"image": "static", "gif": "gifs", "video": "videos"}[kind]

    def _scan_root(self, root: Path, included: bool) -> list[WallpaperItem]:
        items: list[WallpaperItem] = []
        for kind in SUPPORTED_EXTENSIONS:
            folder = root / self.folder_for_kind(kind)
            if not folder.exists():
                continue
            for path in folder.iterdir():
                if path.is_file() and self.kind_for_path(path) == kind:
                    details = self._metadata.get("details", {}).get(self._key(path), {})
                    if isinstance(details, dict) and details:
                        tags = tuple(details.get("tags", []))
                        collection = str(details.get("collection", ""))
                        resource_class = str(details.get("resource_class", "") or "leve")
                    else:
                        analysis = analyze_media(path)
                        tags = analysis.tags
                        collection = ""
                        resource_class = analysis.resource_class
                    items.append(
                        WallpaperItem(
                            kind=kind,
                            path=path,
                            name=path.stem.replace("-", " ").title(),
                            included=included,
                            favorite=self._key(path) in self._metadata["favorites"],
                            recent=self._key(path) in self._metadata["recent"],
                            tags=tags,
                            collection=collection,
                            resource_class=resource_class,
                        )
                    )
        return items

    def _load_metadata(self) -> dict[str, object]:
        try:
            data = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        favorites = data.get("favorites", [])
        recent = data.get("recent", [])
        details = data.get("details", {})
        return {
            "favorites": favorites if isinstance(favorites, list) else [],
            "recent": recent if isinstance(recent, list) else [],
            "details": details if isinstance(details, dict) else {},
        }

    def _save_metadata(self) -> None:
        write_json_atomic(self.metadata_path, self._metadata)

    def _key(self, path: Path) -> str:
        try:
            return str(path.resolve()).lower()
        except OSError:
            return str(path).lower()

    @staticmethod
    def _available_destination(directory: Path, name: str) -> Path:
        destination = directory / name
        if not destination.exists():
            return destination
        stem = Path(name).stem
        suffix = Path(name).suffix
        for index in range(2, 1000):
            destination = directory / f"{stem}-{index}{suffix}"
            if not destination.exists():
                return destination
        raise OSError(f"Nao foi possivel criar um nome livre para {name}")
