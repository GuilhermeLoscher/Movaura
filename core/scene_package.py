from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from core.runtime_paths import data_root
from core.wallpaper_library import WallpaperLibrary
from core.presentation_validator import PresentationValidator
from core.thumbnail_cache import thumbnail_digest


SCENE_FORMAT = "movaura-scene"
SCENE_VERSION = 1
MAX_PACKAGE_ENTRIES = 64
MAX_PACKAGE_UNCOMPRESSED_BYTES = 750 * 1024 * 1024
MAX_MEDIA_BYTES = 650 * 1024 * 1024
ALLOWED_THUMBNAIL_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".webp"}
FORBIDDEN_PACKAGE_SUFFIXES = {
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".js",
    ".lnk",
    ".msi",
    ".ps1",
    ".pyd",
    ".scr",
    ".vbs",
}


@dataclass(frozen=True)
class ScenePackageResult:
    success: bool
    message: str
    settings: dict[str, object] | None = None


class ScenePackageManager:
    def __init__(self, import_root: Path | None = None) -> None:
        self.import_root = import_root or data_root() / "scenes"

    def export_scene(self, destination: Path, settings: dict[str, object]) -> ScenePackageResult:
        media_path = Path(str(settings.get("media_path", ""))).expanduser()
        scene = {
            "format": SCENE_FORMAT,
            "version": SCENE_VERSION,
            "settings": {
                "experience_mode": "animated-desktop",
                "host_mode": "native-composition",
                "native_surface": "desktop-live",
                "renderer": str(settings.get("renderer", "color")),
                "color": str(settings.get("color", "#0078ff")),
                "fps": int(settings.get("fps", 30)),
                "effect_intensity": int(settings.get("effect_intensity", 70)),
                "effect_speed": int(settings.get("effect_speed", 100)),
                "scene_layers": settings.get("scene_layers", []),
                "performance_profile": str(settings.get("performance_profile", "adaptive")),
                "low_power_mode": bool(settings.get("low_power_mode", True)),
                "media_path": "",
            },
        }
        destination = destination.with_suffix(".movaura")
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
                if media_path.is_file() and WallpaperLibrary.kind_for_path(media_path):
                    media_name = f"media/{media_path.name}"
                    archive.write(media_path, media_name)
                    scene["settings"]["media_path"] = media_name
                    for layer in scene["settings"].get("scene_layers", []):
                        if isinstance(layer, dict) and layer.get("kind") == "background":
                            layer["media_path"] = media_name
                    thumbnail = self._thumbnail_for(media_path)
                    if thumbnail:
                        archive.write(thumbnail, f"thumbnail{thumbnail.suffix.lower()}")
                archive.writestr("scene.json", json.dumps(scene, ensure_ascii=False, indent=2))
        except OSError as exc:
            return ScenePackageResult(False, f"Não foi possível exportar a cena: {exc}")
        return ScenePackageResult(True, f"Cena exportada: {destination.name}")

    def import_scene(self, source: Path) -> ScenePackageResult:
        destination = self.import_root / f"imported-{uuid4().hex[:10]}"
        try:
            with zipfile.ZipFile(source) as archive:
                names = set(archive.namelist())
                if "scene.json" not in names:
                    return ScenePackageResult(False, "O pacote não contém uma cena válida.")
                package_error = self._validate_archive_members(archive)
                if package_error:
                    return ScenePackageResult(False, package_error)
                if any(self._unsafe_name(name) for name in names):
                    return ScenePackageResult(False, "O pacote contém caminhos inválidos.")
                scene = json.loads(archive.read("scene.json").decode("utf-8"))
                if scene.get("format") != SCENE_FORMAT or scene.get("version") != SCENE_VERSION:
                    return ScenePackageResult(False, "A versão deste pacote de cena não é compatível.")
                settings = scene.get("settings")
                if not isinstance(settings, dict):
                    return ScenePackageResult(False, "As configurações da cena são inválidas.")
                media_name = str(settings.get("media_path", ""))
                if media_name:
                    if media_name not in names or self._unsafe_name(media_name):
                        return ScenePackageResult(False, "A mídia declarada não foi encontrada no pacote.")
                    info = archive.getinfo(media_name)
                    if info.file_size > MAX_MEDIA_BYTES:
                        return ScenePackageResult(False, "A midia do pacote e grande demais.")
                    if not WallpaperLibrary.kind_for_path(Path(media_name)):
                        return ScenePackageResult(False, "A midia do pacote nao e compativel.")
                    destination.mkdir(parents=True, exist_ok=True)
                    archive.extract(media_name, destination)
                    settings["media_path"] = str(destination / media_name)
                    for layer in settings.get("scene_layers", []):
                        if isinstance(layer, dict) and layer.get("kind") == "background":
                            layer["media_path"] = str(destination / media_name)
                validation = PresentationValidator().validate(settings)
                if not validation.success:
                    if destination.exists():
                        shutil.rmtree(destination, ignore_errors=True)
                    return ScenePackageResult(False, f"A cena importada não é válida: {validation.message}")
                return ScenePackageResult(True, f"Cena importada: {source.name}", settings)
        except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
            if destination.exists():
                shutil.rmtree(destination, ignore_errors=True)
            return ScenePackageResult(False, f"Não foi possível importar a cena: {exc}")

    @staticmethod
    def _unsafe_name(name: str) -> bool:
        path = Path(name)
        return path.is_absolute() or ".." in path.parts or "\\" in name

    @staticmethod
    def _validate_archive_members(archive: zipfile.ZipFile) -> str:
        infos = archive.infolist()
        if len(infos) > MAX_PACKAGE_ENTRIES:
            return "O pacote contem arquivos demais."
        total_size = sum(item.file_size for item in infos)
        if total_size > MAX_PACKAGE_UNCOMPRESSED_BYTES:
            return "O pacote e grande demais para importar com seguranca."
        for item in infos:
            name = item.filename
            if ScenePackageManager._unsafe_name(name):
                return "O pacote contem caminhos invalidos."
            path = Path(name)
            suffix = path.suffix.lower()
            if suffix in FORBIDDEN_PACKAGE_SUFFIXES:
                return "O pacote contem arquivos executaveis ou scripts."
            if name == "scene.json":
                continue
            if name.startswith("media/") and WallpaperLibrary.kind_for_path(path):
                continue
            if path.name.startswith("thumbnail") and suffix in ALLOWED_THUMBNAIL_SUFFIXES:
                continue
            return "O pacote contem arquivos nao permitidos."
        return ""

    @staticmethod
    def _thumbnail_for(media_path: Path) -> Path | None:
        if media_path.suffix.lower() in {".bmp", ".jpeg", ".jpg", ".png", ".webp"}:
            return media_path
        cached = data_root() / "thumbnails" / f"{thumbnail_digest(media_path)}.jpg"
        return cached if cached.is_file() else None
