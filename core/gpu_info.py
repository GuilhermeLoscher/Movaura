from __future__ import annotations

import ctypes
from ctypes import wintypes


DISPLAY_DEVICE_ACTIVE = 0x00000001


class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128),
    ]


def active_display_adapters() -> list[str]:
    user32 = ctypes.windll.user32
    user32.EnumDisplayDevicesW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(DISPLAY_DEVICEW),
        wintypes.DWORD,
    ]
    user32.EnumDisplayDevicesW.restype = wintypes.BOOL
    adapters: list[str] = []
    index = 0
    while True:
        device = DISPLAY_DEVICEW()
        device.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        if not user32.EnumDisplayDevicesW(None, index, ctypes.byref(device), 0):
            break
        if device.StateFlags & DISPLAY_DEVICE_ACTIVE and device.DeviceString:
            name = str(device.DeviceString)
            if name not in adapters:
                adapters.append(name)
        index += 1
    return adapters
