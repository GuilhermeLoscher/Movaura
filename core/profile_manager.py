from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.settings import DEFAULT_SETTINGS, MovauraSettings
from core.json_store import read_json_object, write_json_atomic
from core.runtime_paths import data_root

DEFAULT_PROFILE_NAMES = {
    "default",
    "gif",
    "image",
    "opengl",
    "video",
}


@dataclass(frozen=True)
class Profile:
    name: str
    path: Path
    data: dict[str, Any]


class ProfileManager:
    def __init__(self, profiles_dir: Path | None = None) -> None:
        self.profiles_dir = profiles_dir or data_root() / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.ensure_defaults()

    def list_profiles(self) -> list[Profile]:
        profiles: list[Profile] = []
        for path in sorted(self.profiles_dir.glob("*.json")):
            data = read_json_object(path)
            if isinstance(data, dict):
                self._migrate_experience_mode(data)
                merged = dict(DEFAULT_SETTINGS)
                merged.update(data)
                profiles.append(Profile(path.stem, path, merged))
        return profiles

    def load(self, name: str) -> Profile | None:
        path = self.profiles_dir / f"{self._safe_name(name)}.json"
        if not path.exists():
            return None
        data = read_json_object(path)
        if data is None:
            return None
        merged = dict(DEFAULT_SETTINGS)
        if isinstance(data, dict):
            self._migrate_experience_mode(data)
            merged.update(data)
        return Profile(path.stem, path, merged)

    def save(self, name: str, settings: MovauraSettings | dict[str, Any]) -> Profile:
        path = self.profiles_dir / f"{self._safe_name(name)}.json"
        data = settings.data if isinstance(settings, MovauraSettings) else settings
        profile_data = dict(DEFAULT_SETTINGS)
        profile_data.update(data)
        write_json_atomic(path, profile_data)
        return Profile(path.stem, path, profile_data)

    def delete(self, name: str) -> bool:
        safe_name = self._safe_name(name)
        if safe_name in DEFAULT_PROFILE_NAMES:
            return False
        path = self.profiles_dir / f"{safe_name}.json"
        if not path.exists():
            return False
        path.unlink()
        return True

    def is_default(self, name: str) -> bool:
        return self._safe_name(name) in DEFAULT_PROFILE_NAMES

    def ensure_defaults(self) -> None:
        defaults = {
            "default": {
                "experience_mode": "desktop-static",
                "renderer": "color",
                "color": "#0078ff",
                "host_mode": "system-wallpaper",
                "screen": "all",
            },
            "opengl": {
                "experience_mode": "animated-preview",
                "renderer": "opengl",
                "fps": 30,
                "host_mode": "native-composition",
                "native_surface": "preview",
                "screen": 0,
            },
            "video": {
                "experience_mode": "animated-preview",
                "renderer": "video",
                "media_path": "",
                "host_mode": "native-composition",
                "native_surface": "preview",
                "screen": 0,
            },
            "gif": {
                "experience_mode": "animated-preview",
                "renderer": "gif",
                "media_path": "",
                "host_mode": "native-composition",
                "native_surface": "preview",
                "screen": 0,
            },
            "image": {
                "experience_mode": "desktop-static",
                "renderer": "image",
                "media_path": "",
                "host_mode": "system-wallpaper",
                "native_surface": "preview",
                "screen": "all",
            },
        }

        for name, data in defaults.items():
            path = self.profiles_dir / f"{name}.json"
            if not path.exists():
                profile_data = dict(DEFAULT_SETTINGS)
                profile_data.update(data)
                write_json_atomic(path, profile_data)

    def _safe_name(self, name: str) -> str:
        safe = "".join(char for char in name.strip().lower() if char.isalnum() or char in "-_")
        return safe or "profile"

    def _migrate_experience_mode(self, data: dict[str, Any]) -> None:
        if "experience_mode" in data:
            if data["experience_mode"] == "animated-desktop":
                data["host_mode"] = "native-composition"
                data["native_surface"] = "desktop-live"
            return
        if (
            data.get("renderer") in {"color", "image"}
            and data.get("host_mode") in {"auto", "system-wallpaper"}
        ):
            data["experience_mode"] = "desktop-static"
            data["host_mode"] = "system-wallpaper"
            return
        data["experience_mode"] = "animated-preview"
        data["host_mode"] = "native-composition"
        data["native_surface"] = "preview"
