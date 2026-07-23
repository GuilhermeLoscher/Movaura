from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path

from core.json_store import read_json_object, write_json_atomic
from core.runtime_paths import data_root


@dataclass(frozen=True)
class AppRule:
    executable: str
    action: str = "pause"


class AppRuleManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or data_root() / "app-rules.json"
        self.data = read_json_object(self.path) or {"rules": []}

    def rules(self) -> list[AppRule]:
        result = []
        for item in self.data.get("rules", []):
            if isinstance(item, dict) and item.get("executable"):
                result.append(AppRule(str(item["executable"]).lower(), str(item.get("action", "pause"))))
        return result

    def save(self, rules: list[AppRule]) -> None:
        self.data = {"rules": [{"executable": rule.executable.lower(), "action": rule.action} for rule in rules]}
        write_json_atomic(self.path, self.data)

    def foreground_executable(self) -> str:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return ""
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = kernel32.OpenProcess(0x1000, False, pid.value)
        if not handle:
            return ""
        try:
            size = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return ""
            return Path(buffer.value).name.lower()
        finally:
            kernel32.CloseHandle(handle)

    def foreground_action(self) -> str:
        executable = self.foreground_executable()
        return next((rule.action for rule in self.rules() if rule.executable == executable), "")
