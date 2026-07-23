from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass


class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", wintypes.BYTE),
        ("BatteryFlag", wintypes.BYTE),
        ("BatteryLifePercent", wintypes.BYTE),
        ("SystemStatusFlag", wintypes.BYTE),
        ("BatteryLifeTime", wintypes.DWORD),
        ("BatteryFullLifeTime", wintypes.DWORD),
    ]


@dataclass(frozen=True)
class PowerStatus:
    on_battery: bool | None


class PowerStatusReader:
    def __init__(self) -> None:
        self._kernel32 = ctypes.windll.kernel32
        self._kernel32.GetSystemPowerStatus.argtypes = [
            ctypes.POINTER(SYSTEM_POWER_STATUS)
        ]
        self._kernel32.GetSystemPowerStatus.restype = wintypes.BOOL

    def read(self) -> PowerStatus:
        try:
            status = SYSTEM_POWER_STATUS()
            if not self._kernel32.GetSystemPowerStatus(ctypes.byref(status)):
                return PowerStatus(on_battery=None)
        except Exception:
            return PowerStatus(on_battery=None)
        if status.ACLineStatus == 0:
            return PowerStatus(on_battery=True)
        if status.ACLineStatus == 1:
            return PowerStatus(on_battery=False)
        return PowerStatus(on_battery=None)
