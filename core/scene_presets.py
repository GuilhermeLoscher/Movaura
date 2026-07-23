from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from core.json_store import read_json_object, write_json_atomic
from core.runtime_paths import data_root


class ScenePresetManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or data_root() / "scene-presets.json"

    def names(self) -> list[str]:
        return sorted(self._load())

    def load(self, name: str) -> dict[str, object] | None:
        value = self._load().get(name)
        return deepcopy(value) if isinstance(value, dict) else None

    def save(self, name: str, scene: dict[str, object]) -> None:
        presets = self._load()
        presets[name.strip()[:80]] = deepcopy(scene)
        write_json_atomic(self.path, presets)

    def delete(self, name: str) -> bool:
        presets = self._load()
        if name not in presets:
            return False
        del presets[name]
        write_json_atomic(self.path, presets)
        return True

    def duplicate(self, source: str, destination: str) -> bool:
        scene = self.load(source)
        if not scene:
            return False
        self.save(destination, scene)
        return True

    def _load(self) -> dict[str, dict[str, object]]:
        data = read_json_object(self.path) or {}
        return {
            str(name): value
            for name, value in data.items()
            if isinstance(value, dict)
        }
