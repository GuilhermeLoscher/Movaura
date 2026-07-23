from __future__ import annotations

import ctypes
from ctypes import wintypes
from collections.abc import Callable

from PyQt6.QtCore import QObject, QTimer


WM_HOTKEY = 0x0312
PM_REMOVE = 0x0001
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
VK_P = 0x50
VK_N = 0x4E
VK_R = 0x52


class GlobalHotkeyManager(QObject):
    def __init__(self, actions: dict[int, Callable[[], None]], parent=None) -> None:
        super().__init__(parent)
        self.actions = actions
        self.user32 = ctypes.windll.user32
        self.registered: list[int] = []
        self.timer = QTimer(self)
        self.timer.setInterval(120)
        self.timer.timeout.connect(self._poll)

    def start(self) -> None:
        self.stop()
        for identifier, key in ((1, VK_P), (2, VK_N), (3, VK_R)):
            if self.user32.RegisterHotKey(None, identifier, MOD_CONTROL | MOD_ALT, key):
                self.registered.append(identifier)
        self.timer.start()

    def stop(self) -> None:
        self.timer.stop()
        for identifier in self.registered:
            self.user32.UnregisterHotKey(None, identifier)
        self.registered.clear()

    def _poll(self) -> None:
        message = wintypes.MSG()
        while self.user32.PeekMessageW(ctypes.byref(message), None, WM_HOTKEY, WM_HOTKEY, PM_REMOVE):
            action = self.actions.get(int(message.wParam))
            if action:
                action()
