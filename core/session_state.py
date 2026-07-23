from __future__ import annotations

import ctypes
from ctypes import wintypes


DESKTOP_SWITCHDESKTOP = 0x0100


class SessionStateReader:
    def __init__(self) -> None:
        self._user32 = ctypes.windll.user32
        self._user32.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._user32.OpenInputDesktop.restype = wintypes.HANDLE
        self._user32.SwitchDesktop.argtypes = [wintypes.HANDLE]
        self._user32.SwitchDesktop.restype = wintypes.BOOL
        self._user32.CloseDesktop.argtypes = [wintypes.HANDLE]
        self._user32.CloseDesktop.restype = wintypes.BOOL

    def is_locked(self) -> bool:
        desktop = self._user32.OpenInputDesktop(0, False, DESKTOP_SWITCHDESKTOP)
        if not desktop:
            return False
        try:
            return not bool(self._user32.SwitchDesktop(desktop))
        finally:
            self._user32.CloseDesktop(desktop)
