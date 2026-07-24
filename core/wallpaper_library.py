from __future__ import annotations

import json
import shutil
import hashlib
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from threading import RLock

from core.json_store import preserve_invalid_file, write_json_atomic
from core.media_analyzer import MEDIA_EXTENSIONS, analyze_media
from core.runtime_paths import app_root, data_root


SUPPORTED_EXTENSIONS = MEDIA_EXTENSIONS
LOGGER = logging.getLogger(__name__)
LIBRARY_CATEGORIES = (
    "Anime",
    "Carros",
    "Cyberpunk",
    "Natureza",
    "Minimalista",
    "Sci-Fi",
    "Abstrato",
    "Fantasia",
    "Espaco",
    "Cidades",
    "Gaming",
    "Escuro",
    "Claro",
    "Tecnologia",
    "Outros",
)


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
    category: str = "Outros"
    file_name: str = ""
    extension: str = ""
    size_bytes: int = 0
    modified_at: float = 0.0
    imported_at: float = 0.0
    last_used_at: float = 0.0
    source_hash: str = ""


class WallpaperLibrary:
    def __init__(self) -> None:
        self.included_root = app_root() / "wallpapers"
        self.personal_root = data_root() / "wallpapers"
        self.metadata_path = data_root() / "library.json"
        self.personal_root.mkdir(parents=True, exist_ok=True)
        self._metadata_lock = RLock()
        self._metadata = self._load_metadata()

    def items(self) -> list[WallpaperItem]:
        with self._metadata_lock:
            items: list[WallpaperItem] = []
            items.extend(self._scan_root(self.included_root, included=True))
            items.extend(self._scan_root(self.personal_root, included=False))
            return sorted(items, key=lambda item: (item.kind, item.name.lower()))

    def import_files(self, paths: list[Path]) -> list[WallpaperItem]:
        with self._metadata_lock:
            imported: list[WallpaperItem] = []
            for source in paths:
                kind = self.kind_for_path(source)
                if not kind or not source.is_file():
                    continue
                existing = self.find_duplicate(source)
                if existing:
                    imported.append(existing)
                    continue
                destination_dir = self.personal_root / self.folder_for_kind(kind)
                destination_dir.mkdir(parents=True, exist_ok=True)
                destination = self._available_destination(destination_dir, source.name)
                shutil.copy2(source, destination)
                analysis = analyze_media(destination)
                category = self.category_for(destination, analysis.tags)
                signature = self.file_digest(destination)
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
                        category=category,
                        file_name=destination.name,
                        extension=destination.suffix.lower(),
                        size_bytes=self._safe_size(destination),
                        modified_at=self._safe_mtime(destination),
                        imported_at=self._safe_mtime(destination),
                        source_hash=signature,
                    )
                )
                self.update_details(
                    imported[-1],
                    list(analysis.tags),
                    "Importados",
                    analysis.resource_class,
                    category,
                    signature,
                )
            return imported

    def import_folder(self, folder: Path) -> list[WallpaperItem]:
        if not folder.is_dir():
            return []
        return self.import_files(
            [path for path in folder.rglob("*") if path.is_file() and self.kind_for_path(path)]
        )

    def remove_personal(self, item: WallpaperItem) -> bool:
        with self._metadata_lock:
            if item.included or not item.path.is_file() or not self._is_inside(item.path, self.personal_root):
                return False
            try:
                item.path.unlink()
            except OSError:
                LOGGER.warning("Could not remove personal wallpaper: %s", item.path)
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

    def rename_personal(self, item: WallpaperItem, new_name: str) -> WallpaperItem | None:
        with self._metadata_lock:
            if item.included or not item.path.is_file() or not self._is_inside(item.path, self.personal_root):
                return None
            clean_stem = self._safe_stem(new_name)
            if not clean_stem:
                return None
            if clean_stem.lower() == item.path.stem.lower():
                return item
            destination = self._available_destination(item.path.parent, f"{clean_stem}{item.path.suffix.lower()}")
            old_key = self._key(item.path)
            try:
                item.path.rename(destination)
            except OSError:
                LOGGER.warning("Could not rename personal wallpaper: %s", item.path)
                return None
            new_key = self._key(destination)
            details_store = self._metadata.setdefault("details", {})
            if isinstance(details_store, dict):
                details_store[new_key] = details_store.pop(old_key, {})
            self._metadata["favorites"] = [new_key if key == old_key else key for key in self._metadata["favorites"]]
            self._metadata["recent"] = [new_key if key == old_key else key for key in self._metadata["recent"]]
            self._save_metadata()
            for current in self.items():
                if self._same_file(current.path, destination):
                    return current
            return None

    def toggle_favorite(self, item: WallpaperItem) -> bool:
        with self._metadata_lock:
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
        with self._metadata_lock:
            key = self._key(item.path)
            recent = [current for current in self._metadata["recent"] if current != key]
            self._metadata["recent"] = [key, *recent][:20]
            details = self._metadata.setdefault("details", {}).setdefault(key, {})
            if isinstance(details, dict):
                details["last_used_at"] = time.time()
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
        category: str | None = None,
        source_hash: str | None = None,
    ) -> None:
        with self._metadata_lock:
            key = self._key(item.path)
            clean_tags = sorted({tag.strip()[:40] for tag in tags if tag.strip()})
            clean_resource = (resource_class or item.resource_class or "leve").strip().lower()
            if clean_resource not in {"leve", "medio", "pesado"}:
                clean_resource = "leve"
            clean_category = self._clean_category(category or self.category_for(item.path, clean_tags))
            payload = {
                "tags": clean_tags[:20],
                "collection": collection.strip()[:80],
                "resource_class": clean_resource,
                "category": clean_category,
                "file_name": item.path.name,
                "extension": item.path.suffix.lower(),
                "size_bytes": self._safe_size(item.path),
                "modified_at": self._safe_mtime(item.path),
            }
            previous = self._metadata.get("details", {}).get(key, {})
            if isinstance(previous, dict):
                payload["imported_at"] = float(previous.get("imported_at", 0.0) or self._safe_mtime(item.path))
                payload["last_used_at"] = float(previous.get("last_used_at", 0.0) or 0.0)
            else:
                payload["imported_at"] = self._safe_mtime(item.path)
                payload["last_used_at"] = 0.0
            if source_hash:
                payload["source_hash"] = source_hash
            elif isinstance(previous, dict) and previous.get("source_hash"):
                payload["source_hash"] = str(previous["source_hash"])
            self._metadata.setdefault("details", {})[key] = payload
            self._save_metadata()

    def ui_state(self) -> dict[str, str]:
        state = self._metadata.get("ui", {})
        return state if isinstance(state, dict) else {}

    def update_ui_state(self, **values: str) -> None:
        with self._metadata_lock:
            state = self._metadata.setdefault("ui", {})
            if not isinstance(state, dict):
                state = {}
                self._metadata["ui"] = state
            for key, value in values.items():
                state[str(key)] = str(value)
            self._save_metadata()

    def find_duplicate(self, source: Path) -> WallpaperItem | None:
        digest = self.file_digest(source)
        if not digest:
            return None
        for item in self.items():
            if self._same_file(source, item.path):
                return item
            details = self._metadata.get("details", {}).get(self._key(item.path), {})
            if (
                isinstance(details, dict)
                and details.get("source_hash") == digest
                and self._same_content(source, item.path)
            ):
                return item
            try:
                if item.path.name == source.name and item.path.stat().st_size == source.stat().st_size:
                    if self.file_digest(item.path) == digest and self._same_content(source, item.path):
                        return item
            except OSError:
                continue
        return None

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
        with self._metadata_lock:
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
    def category_for(path: Path, tags: tuple[str, ...] | list[str] = ()) -> str:
        haystack = " ".join([path.stem, *[str(tag) for tag in tags]]).lower()
        mapping = (
            ("Anime", ("anime", "manga", "waifu")),
            ("Carros", ("carro", "carros", "car", "cars", "automotive", "vehicle")),
            ("Cyberpunk", ("cyberpunk", "neon", "futurista", "future")),
            ("Natureza", ("natureza", "nature", "forest", "floresta", "water", "ocean", "mountain")),
            ("Minimalista", ("minimal", "minimalista", "clean")),
            ("Sci-Fi", ("sci-fi", "scifi", "space station", "spaceship")),
            ("Abstrato", ("abstract", "abstrato", "shape", "gradient")),
            ("Fantasia", ("fantasia", "fantasy", "dragon", "magic")),
            ("Espaco", ("espaco", "space", "galaxy", "planet", "cosmos")),
            ("Cidades", ("cidade", "cidades", "city", "urban", "skyline")),
            ("Gaming", ("game", "gaming", "gamer", "rpg", "fps")),
            ("Escuro", ("dark", "escuro", "black", "noir")),
            ("Claro", ("light", "claro", "white", "bright")),
            ("Tecnologia", ("tech", "tecnologia", "circuit", "digital")),
        )
        for category, markers in mapping:
            if any(marker in haystack for marker in markers):
                return category
        return "Outros"

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
                        category = self._clean_category(
                            str(details.get("category", "") or self.category_for(path, tags))
                        )
                        imported_at = float(details.get("imported_at", 0.0) or 0.0)
                        last_used_at = float(details.get("last_used_at", 0.0) or 0.0)
                        source_hash = str(details.get("source_hash", "") or "")
                    else:
                        analysis = analyze_media(path)
                        tags = analysis.tags
                        collection = ""
                        resource_class = analysis.resource_class
                        category = self.category_for(path, tags)
                        imported_at = 0.0
                        last_used_at = 0.0
                        source_hash = ""
                    file_name = path.name
                    extension = path.suffix.lower()
                    size_bytes = self._safe_size(path)
                    modified_at = self._safe_mtime(path)
                    imported_at = imported_at or modified_at
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
                            category=category,
                            file_name=file_name,
                            extension=extension,
                            size_bytes=size_bytes,
                            modified_at=modified_at,
                            imported_at=imported_at,
                            last_used_at=last_used_at,
                            source_hash=source_hash,
                        )
                    )
        return items

    def _load_metadata(self) -> dict[str, object]:
        try:
            data = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            backup = preserve_invalid_file(self.metadata_path)
            LOGGER.warning("Library metadata was invalid and was preserved at %s", backup)
            data = {}
        except OSError:
            data = {}
        favorites = data.get("favorites", [])
        recent = data.get("recent", [])
        details = data.get("details", {})
        ui = data.get("ui", {})
        return {
            "favorites": favorites if isinstance(favorites, list) else [],
            "recent": recent if isinstance(recent, list) else [],
            "details": details if isinstance(details, dict) else {},
            "ui": ui if isinstance(ui, dict) else {},
        }

    def _save_metadata(self) -> None:
        with self._metadata_lock:
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

    @staticmethod
    def file_digest(path: Path) -> str:
        try:
            size = path.stat().st_size
            digest = hashlib.sha256()
            with path.open("rb") as file:
                digest.update(file.read(1024 * 1024))
                if size > 2 * 1024 * 1024:
                    file.seek(max(0, size - 1024 * 1024))
                    digest.update(file.read(1024 * 1024))
            return f"{size}:{digest.hexdigest()}"
        except OSError:
            return ""

    @staticmethod
    def full_file_digest(path: Path) -> str:
        try:
            digest = hashlib.sha256()
            with path.open("rb") as file:
                for chunk in iter(lambda: file.read(1024 * 1024), b""):
                    digest.update(chunk)
            return digest.hexdigest()
        except OSError:
            return ""

    @staticmethod
    def _clean_category(value: str) -> str:
        return value if value in LIBRARY_CATEGORIES else "Outros"

    @staticmethod
    def _safe_stem(value: str) -> str:
        clean = re.sub(r"[^A-Za-z0-9 ._-]+", "", value.strip()).strip(" ._-")
        return clean[:80]

    @staticmethod
    def _same_file(first: Path, second: Path) -> bool:
        try:
            return first.resolve() == second.resolve()
        except OSError:
            return False

    @classmethod
    def _same_content(cls, first: Path, second: Path) -> bool:
        try:
            if first.stat().st_size != second.stat().st_size:
                return False
        except OSError:
            return False
        return cls.full_file_digest(first) == cls.full_file_digest(second)

    @staticmethod
    def _is_inside(path: Path, root: Path) -> bool:
        try:
            path.resolve().relative_to(root.resolve())
            return True
        except (OSError, ValueError):
            return False

    @staticmethod
    def _safe_size(path: Path) -> int:
        try:
            return path.stat().st_size
        except OSError:
            return 0

    @staticmethod
    def _safe_mtime(path: Path) -> float:
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0
