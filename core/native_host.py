from __future__ import annotations

import ctypes
from dataclasses import dataclass
from pathlib import Path

from core.runtime_paths import resource_root

class NwWindowInfo(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_uint64),
        ("pid", ctypes.c_uint32),
        ("left", ctypes.c_int32),
        ("top", ctypes.c_int32),
        ("right", ctypes.c_int32),
        ("bottom", ctypes.c_int32),
        ("visible", ctypes.c_int32),
    ]


class NwDesktopReport(ctypes.Structure):
    _fields_ = [
        ("progman", NwWindowInfo),
        ("shell_defview", NwWindowInfo),
        ("sys_listview", NwWindowInfo),
        ("workerw_with_defview", NwWindowInfo),
        ("workerw_after_defview", NwWindowInfo),
        ("wallpaper_workerw", NwWindowInfo),
        ("workerw_count", ctypes.c_int32),
        ("send_ok", ctypes.c_int32),
        ("last_error", ctypes.c_uint64),
    ]


class NwAttachResult(ctypes.Structure):
    _fields_ = [
        ("success", ctypes.c_int32),
        ("parent_hwnd", ctypes.c_uint64),
        ("last_error", ctypes.c_uint64),
    ]


@dataclass(frozen=True)
class NativeHostStatus:
    loaded: bool
    path: Path | None
    message: str


class NativeHost:
    def __init__(self, dll_path: Path | None = None) -> None:
        self.dll_path = dll_path or self.default_dll_path()
        self.dll = None
        self.status = self._load()

    @staticmethod
    def default_dll_path() -> Path:
        root = resource_root()
        candidates = [
            root / "native_host" / "bin" / "movaura_native_host.dll",
            root / "native_host" / "build-nmake" / "bin" / "movaura_native_host.dll",
            root / "native_host" / "build" / "bin" / "Release" / "movaura_native_host.dll",
            root / "native_host" / "build" / "bin" / "Debug" / "movaura_native_host.dll",
            root / "native_host" / "build" / "bin" / "movaura_native_host.dll",
            root / "native_host" / "movaura_native_host.dll",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def probe_text(self) -> str:
        if not self.status.loaded:
            return self.status.message

        report = NwDesktopReport()
        ok = self.dll.nw_probe_desktop(ctypes.byref(report))
        lines = ["Movaura native host diagnostics:"]
        lines.append(f"loaded: {self.dll_path}")
        lines.append(f"probe_ok: {bool(ok)}")
        lines.append(_format_window("Progman", report.progman))
        lines.append(_format_window("SHELLDLL_DefView", report.shell_defview))
        lines.append(_format_window("SysListView32", report.sys_listview))
        lines.append(_format_window("WorkerW with DefView", report.workerw_with_defview))
        lines.append(_format_window("WorkerW after DefView", report.workerw_after_defview))
        lines.append(_format_window("Wallpaper WorkerW", report.wallpaper_workerw))
        lines.append(f"WorkerW count: {report.workerw_count}")
        lines.append(f"Send workerw messages ok: {bool(report.send_ok)}")
        lines.append(f"Last error: {report.last_error}")
        return "\n".join(lines)

    def attach_to_workerw_after_defview(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> NwAttachResult | None:
        if not self.status.loaded:
            return None

        result = NwAttachResult()
        self.dll.nw_attach_to_workerw_after_defview(
            ctypes.c_uint64(hwnd),
            ctypes.c_int32(x),
            ctypes.c_int32(y),
            ctypes.c_int32(width),
            ctypes.c_int32(height),
            ctypes.byref(result),
        )
        return result

    def attach_to_progman_stack(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> NwAttachResult | None:
        if not self.status.loaded:
            return None

        result = NwAttachResult()
        self.dll.nw_attach_to_progman_stack(
            ctypes.c_uint64(hwnd),
            ctypes.c_int32(x),
            ctypes.c_int32(y),
            ctypes.c_int32(width),
            ctypes.c_int32(height),
            ctypes.byref(result),
        )
        return result

    def _load(self) -> NativeHostStatus:
        if not self.dll_path.exists():
            return NativeHostStatus(
                loaded=False,
                path=self.dll_path,
                message=f"Native host DLL not found: {self.dll_path}",
            )

        try:
            self.dll = ctypes.WinDLL(str(self.dll_path))
        except OSError as exc:
            return NativeHostStatus(False, self.dll_path, f"Native host load failed: {exc}")

        self.dll.nw_probe_desktop.argtypes = [ctypes.POINTER(NwDesktopReport)]
        self.dll.nw_probe_desktop.restype = ctypes.c_int32
        self.dll.nw_send_workerw_messages.argtypes = []
        self.dll.nw_send_workerw_messages.restype = ctypes.c_int32
        self.dll.nw_attach_to_workerw_after_defview.argtypes = [
            ctypes.c_uint64,
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.POINTER(NwAttachResult),
        ]
        self.dll.nw_attach_to_workerw_after_defview.restype = ctypes.c_int32
        self.dll.nw_attach_to_progman_stack.argtypes = [
            ctypes.c_uint64,
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.c_int32,
            ctypes.POINTER(NwAttachResult),
        ]
        self.dll.nw_attach_to_progman_stack.restype = ctypes.c_int32

        return NativeHostStatus(True, self.dll_path, f"Native host loaded: {self.dll_path}")


def _format_window(label: str, info: NwWindowInfo) -> str:
    if not info.hwnd:
        return f"{label}: not found"

    width = info.right - info.left
    height = info.bottom - info.top
    return (
        f"{label}: hwnd={info.hwnd} pid={info.pid} visible={bool(info.visible)} "
        f"rect=({info.left}, {info.top}, {info.right}, {info.bottom}) "
        f"size={width}x{height}"
    )
