from __future__ import annotations

from pathlib import Path
from typing import Any

from core.json_store import read_json_object, write_json_atomic
from core.runtime_paths import data_root
from core.wallpaper_library import WallpaperLibrary


class MonitorProfileManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or data_root() / "monitor-profiles.json"

    def profiles(self) -> dict[str, dict[str, dict[str, str]]]:
        data = read_json_object(self.path) or {}
        profiles = data.get("profiles", {})
        return profiles if isinstance(profiles, dict) else {}

    def save(self, name: str, assignments: dict[str, dict[str, str]]) -> str:
        safe_name = self._safe_name(name)
        profiles = self.profiles()
        profiles[safe_name] = assignments
        write_json_atomic(self.path, {"profiles": profiles})
        return safe_name

    def delete(self, name: str) -> bool:
        profiles = self.profiles()
        if name not in profiles:
            return False
        del profiles[name]
        write_json_atomic(self.path, {"profiles": profiles})
        return True

    @staticmethod
    def assignment_for_path(path: str) -> dict[str, str]:
        media_path = str(Path(path).expanduser())
        kind = WallpaperLibrary.kind_for_path(Path(media_path)) or "color"
        return {"renderer": kind, "media_path": media_path}

    @staticmethod
    def _safe_name(name: str) -> str:
        safe = "".join(char for char in name.strip().lower() if char.isalnum() or char in "-_")
        return safe or "perfil-monitores"
