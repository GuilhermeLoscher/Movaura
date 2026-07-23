from __future__ import annotations

import sys
import winreg
from dataclasses import dataclass
from pathlib import Path

from core.runtime_paths import app_root, is_frozen


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "Movaura"


@dataclass(frozen=True)
class StartupResult:
    success: bool
    message: str


class StartupManager:
    def __init__(self) -> None:
        self.root = app_root()
        self.launcher = self.root / "MovauraStartup.vbs"

    def is_enabled(self) -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                value, _ = winreg.QueryValueEx(key, VALUE_NAME)
        except OSError:
            return False
        return str(value) == self.command

    def set_enabled(self, enabled: bool) -> StartupResult:
        try:
            if enabled:
                if not is_frozen() and not self.launcher.exists():
                    return StartupResult(
                        False,
                        f"Inicializador automático não encontrado: {self.launcher}",
                    )
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                    winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, self.command)
                return StartupResult(True, "O Movaura será iniciado com o Windows.")

            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    RUN_KEY,
                    0,
                    winreg.KEY_SET_VALUE,
                ) as key:
                    winreg.DeleteValue(key, VALUE_NAME)
            except FileNotFoundError:
                pass
            return StartupResult(True, "Inicialização do Movaura com o Windows desativada.")
        except OSError as exc:
            return StartupResult(
                False,
                f"Não foi possível atualizar a inicialização do Windows: {exc}",
            )

    @property
    def command(self) -> str:
        if is_frozen():
            return f'"{Path(sys.executable).resolve()}" --startup'
        return f'wscript.exe "{self.launcher}"'
