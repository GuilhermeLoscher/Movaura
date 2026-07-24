from __future__ import annotations

import ctypes
import shutil
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path

import winreg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from core.native_compositor import NativeCompositorLauncher
from core.runtime_paths import app_root, is_frozen
from core.settings import MovauraSettings


@dataclass(frozen=True)
class ScreensaverResult:
    success: bool
    message: str


class ScreensaverManager:
    @staticmethod
    def target_path() -> Path:
        return app_root() / "Movaura.scr"

    def install(self) -> ScreensaverResult:
        if not is_frozen():
            return ScreensaverResult(False, "Instale o Movaura antes de ativar o protetor de tela.")
        target = self.target_path()
        if not target.exists():
            try:
                shutil.copy2(Path(__import__("sys").executable), target)
            except OSError as exc:
                return ScreensaverResult(False, f"Falha ao preparar protetor de tela: {exc}")
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "SCRNSAVE.EXE", 0, winreg.REG_SZ, str(target))
                winreg.SetValueEx(key, "ScreenSaveActive", 0, winreg.REG_SZ, "1")
        except OSError as exc:
            return ScreensaverResult(False, f"Falha ao ativar protetor de tela: {exc}")
        return ScreensaverResult(True, "Movaura ativado como protetor de tela do Windows.")


class ScreensaverSession:
    def __init__(self, app: QApplication, settings: MovauraSettings) -> None:
        self.app = app
        self.settings = settings
        self.launcher = NativeCompositorLauncher()
        self.initial_cursor = self._cursor()
        self.tick_count = 0
        self.timer = QTimer()
        self.timer.setInterval(180)
        self.timer.timeout.connect(self._check_exit)

    def start(self) -> bool:
        result = self.launcher.launch_renderer(
            renderer=self.settings.get_str("renderer"),
            color=self.settings.get_str("color"),
            fps=self.settings.get_int("fps"),
            media_path=self.settings.get_str("media_path"),
            fullscreen=True,
        )
        if not result.success:
            return False
        self.timer.start()
        self.app.aboutToQuit.connect(self.launcher.stop)
        return True

    def _check_exit(self) -> None:
        self.tick_count += 1
        if self.tick_count < 5:
            return
        if self._cursor() != self.initial_cursor or any(ctypes.windll.user32.GetAsyncKeyState(code) & 0x8000 for code in range(8, 255)):
            self.app.quit()

    @staticmethod
    def _cursor() -> tuple[int, int]:
        point = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y
