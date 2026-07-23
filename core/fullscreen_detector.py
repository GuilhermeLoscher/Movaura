from __future__ import annotations

import ctypes
from ctypes import wintypes

import win32con
import win32gui
import win32process


IGNORED_CLASSES = {
    "Progman",
    "Shell_TrayWnd",
    "WorkerW",
}

MONITOR_DEFAULTTONEAREST = 2


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


user32 = ctypes.windll.user32
user32.IsZoomed.argtypes = [wintypes.HWND]
user32.IsZoomed.restype = wintypes.BOOL
user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
user32.MonitorFromWindow.restype = wintypes.HANDLE
# GetMonitorInfoW accepts MONITORINFO and its extended MONITORINFOEXW variant.
# Keep the shared ctypes declaration generic so the monitor manager can request
# the display device name without conflicting with fullscreen detection.
user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
user32.GetMonitorInfoW.restype = wintypes.BOOL
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
user32.GetWindowRect.restype = wintypes.BOOL


class FullscreenAppDetector:
    def has_foreground_fullscreen_app(self, ignored_pids: set[int] | None = None) -> bool:
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd or not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
                return False
            if win32gui.GetClassName(hwnd) in IGNORED_CLASSES:
                return False

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if ignored_pids and pid in ignored_pids:
                return False

            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            standard_frame = style & win32con.WS_OVERLAPPEDWINDOW
            if user32.IsZoomed(hwnd) and standard_frame:
                return False

            monitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
            if not monitor:
                return False
            monitor_info = MONITORINFO()
            monitor_info.cbSize = ctypes.sizeof(MONITORINFO)
            window_rect = RECT()
            if not user32.GetMonitorInfoW(monitor, ctypes.byref(monitor_info)):
                return False
            if not user32.GetWindowRect(hwnd, ctypes.byref(window_rect)):
                return False
        except Exception:
            return False

        return self._covers_monitor(
            self._rect_tuple(window_rect),
            self._rect_tuple(monitor_info.rcMonitor),
        )

    @staticmethod
    def _rect_tuple(rect: RECT) -> tuple[int, int, int, int]:
        return rect.left, rect.top, rect.right, rect.bottom

    @staticmethod
    def _covers_monitor(
        window_rect: tuple[int, int, int, int],
        monitor_rect: tuple[int, int, int, int],
        tolerance: int = 2,
    ) -> bool:
        left, top, right, bottom = window_rect
        monitor_left, monitor_top, monitor_right, monitor_bottom = monitor_rect
        return (
            left <= monitor_left + tolerance
            and top <= monitor_top + tolerance
            and right >= monitor_right - tolerance
            and bottom >= monitor_bottom - tolerance
        )
