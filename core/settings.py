from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.json_store import preserve_invalid_file, read_json_object, write_json_atomic
from core.runtime_paths import data_root


DEFAULT_SETTINGS = {
    "experience_mode": "desktop-static",
    "host_mode": "auto",
    "renderer": "color",
    "selected_profile": "default",
    "media_path": "",
    "wallpaper_position": "fill",
    "color": "#0078ff",
    "fps": 30,
    "effect_intensity": 70,
    "effect_speed": 100,
    "scene_layers": [],
    "screen": "all",
    "multi_monitor_mode": "repeat",
    "monitor_profile": "",
    "monitor_assignments": {},
    "native_surface": "preview",
    "start_with_windows": False,
    "tray_enabled": True,
    "plugins_enabled": True,
    "pause_when_fullscreen_app": True,
    "low_power_mode": True,
    "optimize_videos": True,
    "auto_performance_enabled": True,
    "auto_cpu_warning_percent": 12,
    "auto_cpu_high_percent": 18,
    "auto_memory_high_mb": 260,
    "pause_on_battery_saver": False,
    "performance_profile": "adaptive",
    "update_manifest_url": "",
    "catalog_manifest_url": "",
    "telemetry_enabled": False,
    "telemetry_endpoint": "",
    "license_required": False,
    "license_supabase_url": "",
    "license_supabase_anon_key": "",
    "license_table": "beta_keys",
    "license_activation_rpc": "activate_beta_key",
    "playlist_enabled": False,
    "active_playlist": "default",
    "global_hotkeys_enabled": True,
    "app_rules_enabled": True,
    "ai_generation_provider": "mock",
    "ai_generation_style": "cinematic",
    "ai_generation_quality": "recommended",
    "ai_generation_resolution": "Full HD 1920x1080",
    "ai_generation_quantity": 1,
    "ai_generation_auto_enhance": True,
}

NON_PERSISTENT_NATIVE_SURFACES = {
    "desktop-experimental",
}


@dataclass
class MovauraSettings:
    path: Path
    data: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_SETTINGS))

    @classmethod
    def load_default(cls) -> "MovauraSettings":
        path = data_root() / "settings.json"
        return cls.load(path)

    @classmethod
    def load(cls, path: Path) -> "MovauraSettings":
        path.parent.mkdir(parents=True, exist_ok=True)
        data = dict(DEFAULT_SETTINGS)

        if path.exists():
            loaded = read_json_object(path)
            if loaded is None:
                backup = preserve_invalid_file(path)
                print(
                    "Configurações inválidas; usando valores padrão. "
                    f"Cópia preservada em: {backup or path}"
                )
            else:
                data.update(loaded)
        if data.get("experience_mode") == "animated-desktop":
            data["host_mode"] = "native-composition"
            data["native_surface"] = "desktop-live"
        return cls(path=path, data=data)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        persisted_data = dict(self.data)
        if persisted_data.get("native_surface") in NON_PERSISTENT_NATIVE_SURFACES:
            persisted_data["native_surface"] = DEFAULT_SETTINGS["native_surface"]
        write_json_atomic(self.path, persisted_data)

    def get_str(self, key: str) -> str:
        return str(self.data.get(key, DEFAULT_SETTINGS.get(key, "")))

    def get_int(self, key: str) -> int:
        value = self.data.get(key, DEFAULT_SETTINGS.get(key, 0))
        try:
            return int(value)
        except (TypeError, ValueError):
            return int(DEFAULT_SETTINGS.get(key, 0))

    def get_bool(self, key: str) -> bool:
        return bool(self.data.get(key, DEFAULT_SETTINGS.get(key, False)))
