from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass

from PyQt6.QtCore import QRect


MONITORINFOF_PRIMARY = 0x00000001
MDT_EFFECTIVE_DPI = 0


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32),
    ]


@dataclass(frozen=True)
class MonitorInfo:
    index: int
    name: str
    geometry: QRect
    device_pixel_ratio: float
    primary: bool

    @property
    def x(self) -> int:
        return self.geometry.x()

    @property
    def y(self) -> int:
        return self.geometry.y()

    @property
    def width(self) -> int:
        return self.geometry.width()

    @property
    def height(self) -> int:
        return self.geometry.height()

    def to_text(self) -> str:
        return (
            f"[{self.index}] {self.name} "
            f"{self.width}x{self.height}+{self.x}+{self.y} "
            f"dpr={self.device_pixel_ratio} primary={self.primary}"
        )


class MonitorManager:
    def monitors(self) -> list[MonitorInfo]:
        result: list[MonitorInfo] = []
        user32 = ctypes.windll.user32
        callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),
            wintypes.LPARAM,
        )

        @callback_type
        def visit(monitor, _hdc, _rect, _lparam):
            info = MONITORINFOEXW()
            info.cbSize = ctypes.sizeof(MONITORINFOEXW)
            if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                return True
            rect = info.rcMonitor
            result.append(
                MonitorInfo(
                    index=len(result),
                    name=info.szDevice,
                    geometry=QRect(
                        rect.left,
                        rect.top,
                        rect.right - rect.left,
                        rect.bottom - rect.top,
                    ),
                    device_pixel_ratio=self._device_pixel_ratio(monitor),
                    primary=bool(info.dwFlags & MONITORINFOF_PRIMARY),
                )
            )
            return True

        user32.EnumDisplayMonitors(None, None, visit, 0)

        return result

    @staticmethod
    def _device_pixel_ratio(monitor) -> float:
        try:
            shcore = ctypes.windll.shcore
            dpi_x = wintypes.UINT()
            dpi_y = wintypes.UINT()
            if shcore.GetDpiForMonitor(monitor, MDT_EFFECTIVE_DPI, ctypes.byref(dpi_x), ctypes.byref(dpi_y)) == 0:
                return round(dpi_x.value / 96.0, 2)
        except (AttributeError, OSError):
            pass
        return 1.0

    def select(self, screen_setting) -> list[MonitorInfo]:
        monitors = self.monitors()
        if screen_setting == "all":
            return monitors

        try:
            index = int(screen_setting)
        except (TypeError, ValueError):
            return monitors

        return [monitor for monitor in monitors if monitor.index == index]
