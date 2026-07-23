from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.json_store import read_json_object, write_json_atomic
from core.runtime_paths import data_root
from core.wallpaper_library import WallpaperLibrary


@dataclass(frozen=True)
class PlaylistEntry:
    path: str
    duration_seconds: int = 60


class PlaylistManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or data_root() / "playlists.json"
        self.data = read_json_object(self.path) or {"playlists": {"default": []}}
        if not isinstance(self.data.get("playlists"), dict):
            self.data = {"playlists": {"default": []}}

    def names(self) -> list[str]:
        return sorted(self.data["playlists"])

    def entries(self, name: str) -> list[PlaylistEntry]:
        raw_entries = self.data["playlists"].get(name, [])
        result = []
        for raw in raw_entries if isinstance(raw_entries, list) else []:
            if isinstance(raw, dict) and raw.get("path"):
                result.append(
                    PlaylistEntry(
                        path=str(raw["path"]),
                        duration_seconds=max(5, int(raw.get("duration_seconds", 60))),
                    )
                )
        return result

    def save(self, name: str, entries: list[PlaylistEntry]) -> None:
        safe_name = name.strip() or "default"
        self.data["playlists"][safe_name] = [
            {"path": entry.path, "duration_seconds": max(5, entry.duration_seconds)}
            for entry in entries
        ]
        write_json_atomic(self.path, self.data)

    def delete(self, name: str) -> bool:
        if name == "default" or name not in self.data["playlists"]:
            return False
        del self.data["playlists"][name]
        write_json_atomic(self.path, self.data)
        return True

    @staticmethod
    def presentation_for(entry: PlaylistEntry) -> dict[str, Any] | None:
        path = Path(entry.path).expanduser()
        kind = WallpaperLibrary.kind_for_path(path)
        if not kind or not path.is_file():
            return None
        return {
            "experience_mode": "animated-desktop",
            "host_mode": "native-composition",
            "native_surface": "desktop-live",
            "renderer": kind,
            "media_path": str(path),
        }
