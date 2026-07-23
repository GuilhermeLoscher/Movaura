from __future__ import annotations

import atexit
import ctypes
from ctypes import wintypes


ERROR_ALREADY_EXISTS = 183
MUTEX_NAME = "Local\\MovauraEngine"


class SingleInstanceGuard:
    def __init__(self, name: str = MUTEX_NAME) -> None:
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32.CreateMutexW.argtypes = [
            wintypes.LPVOID,
            wintypes.BOOL,
            wintypes.LPCWSTR,
        ]
        self._kernel32.CreateMutexW.restype = wintypes.HANDLE
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL
        ctypes.set_last_error(0)
        self._handle = self._kernel32.CreateMutexW(None, False, name)
        self.already_running = (
            not self._handle or ctypes.get_last_error() == ERROR_ALREADY_EXISTS
        )
        atexit.register(self.close)

    def close(self) -> None:
        if self._handle:
            self._kernel32.CloseHandle(self._handle)
            self._handle = None
