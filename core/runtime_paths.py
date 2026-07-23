from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_root() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_root() -> Path:
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", app_root())).resolve()
    return app_root()


def app_icon_path() -> Path:
    return resource_root() / "assets" / "movaura.ico"


def app_logo_path() -> Path:
    return resource_root() / "assets" / "movaura-logo.png"


def data_root() -> Path:
    if not is_frozen():
        return app_root() / "data"
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Movaura"
    return Path.home() / "AppData" / "Local" / "Movaura"
