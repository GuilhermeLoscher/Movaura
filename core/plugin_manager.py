from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.runtime_paths import resource_root


@dataclass
class PluginInfo:
    name: str
    path: Path
    module: Any


class PluginManager:
    def __init__(self, plugins_dir: Path | None = None) -> None:
        self.plugins_dir = plugins_dir or resource_root() / "plugins"
        self.plugins: list[PluginInfo] = []

    def discover(self) -> list[PluginInfo]:
        self.plugins = []
        if not self.plugins_dir.exists():
            return self.plugins

        for plugin_file in sorted(self.plugins_dir.glob("*/plugin.py")):
            plugin = self._load_plugin(plugin_file)
            if plugin:
                self.plugins.append(plugin)

        return self.plugins

    def renderer_factories(self) -> dict[str, Any]:
        factories: dict[str, Any] = {}
        for plugin in self.plugins:
            register = getattr(plugin.module, "register", None)
            if not callable(register):
                continue

            try:
                data = register()
            except Exception as exc:
                print(f"Plugin {plugin.name} register failed: {exc}")
                continue

            if isinstance(data, dict):
                factories.update(data.get("renderers", {}))

        return factories

    def _load_plugin(self, plugin_file: Path) -> PluginInfo | None:
        plugin_root = self.plugins_dir.resolve()
        resolved = plugin_file.resolve()
        try:
            resolved.relative_to(plugin_root)
        except ValueError:
            print(f"Plugin path rejected outside plugin root: {resolved}")
            return None
        name = plugin_file.parent.name
        spec = importlib.util.spec_from_file_location(f"movaura_plugin_{name}", plugin_file)
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            print(f"Plugin {name} load failed: {exc}")
            return None

        return PluginInfo(name=name, path=plugin_file, module=module)
