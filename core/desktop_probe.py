from __future__ import annotations

import ctypes
from dataclasses import dataclass, field
from typing import Callable

import win32con
import win32gui
import win32process


SHELL_SPAWN_WORKERW = 0x052C


@dataclass(frozen=True)
class WindowInfo:
    hwnd: int
    class_name: str
    title: str
    parent: int
    pid: int
    visible: bool
    rect: tuple[int, int, int, int]

    @property
    def size(self) -> str:
        left, top, right, bottom = self.rect
        return f"{right - left}x{bottom - top}"


@dataclass
class DesktopReport:
    progman: WindowInfo | None = None
    shell_defview: WindowInfo | None = None
    sys_listview: WindowInfo | None = None
    workerws: list[WindowInfo] = field(default_factory=list)
    workerw_with_defview: WindowInfo | None = None
    workerw_after_defview: WindowInfo | None = None
    wallpaper_workerw: WindowInfo | None = None
    rejected_workerws: list[str] = field(default_factory=list)
    workerw_messages: list[str] = field(default_factory=list)
    send_message_ok: bool | None = None
    send_message_result: int | None = None

    @property
    def host_capability(self) -> str:
        if self.workerw_after_defview:
            if self.workerw_after_defview.parent:
                return "nested-workerw: detected, but Explorer paints an opaque desktop layer above it"
            return "classic-workerw: compatible desktop host detected"
        if self.progman and self.shell_defview and self.shell_defview.parent == self.progman.hwnd:
            return "progman-defview: no safe live-wallpaper window layer is exposed"
        return "unsupported: no safe live-wallpaper window layer was detected"

    def to_text(self) -> str:
        lines = ["Movaura desktop diagnostics:"]
        lines.append(_format_window("Progman", self.progman))
        lines.append(_format_window("SHELLDLL_DefView", self.shell_defview))
        lines.append(_format_window("SysListView32", self.sys_listview))
        lines.append(_format_window("WorkerW with DefView", self.workerw_with_defview))
        lines.append(_format_window("WorkerW after DefView", self.workerw_after_defview))
        lines.append(_format_window("Wallpaper WorkerW", self.wallpaper_workerw))
        lines.append(f"Desktop host capability: {self.host_capability}")
        if self.rejected_workerws:
            lines.append("Rejected WorkerW candidates:")
            lines.extend(f"  {reason}" for reason in self.rejected_workerws)
        if self.workerw_messages:
            lines.append("WorkerW spawn messages:")
            lines.extend(f"  {message}" for message in self.workerw_messages)
        lines.append(
            "SendMessageTimeoutW(0x052C): "
            f"ok={self.send_message_ok} result={self.send_message_result}"
        )
        lines.append(f"WorkerW count: {len(self.workerws)}")

        for index, workerw in enumerate(self.workerws, start=1):
            lines.append(f"  WorkerW[{index}]: {_window_summary(workerw)}")

        return "\n".join(lines)


class DesktopProbe:
    def probe(self, refresh_workerw: bool = False) -> DesktopReport:
        if refresh_workerw:
            workerw_messages = self.request_workerw()
            send_ok = any(ok for _, _, ok, _ in workerw_messages)
            send_result = workerw_messages[-1][3] if workerw_messages else 0
        else:
            workerw_messages = []
            send_ok = None
            send_result = None

        report = DesktopReport(send_message_ok=send_ok, send_message_result=send_result)
        report.workerw_messages = [
            f"wParam={wparam} lParam={lparam} ok={ok} result={result}"
            for wparam, lparam, ok, result in workerw_messages
        ]
        report.progman = self._get_progman()
        report.workerws = self._find_top_level_by_class("WorkerW")

        shell_parent = report.progman.hwnd if report.progman else 0
        report.shell_defview = self._find_child(shell_parent, "SHELLDLL_DefView")
        if report.shell_defview is None:
            report.workerw_with_defview = self._find_workerw_with_defview(report.workerws)
            if report.workerw_with_defview:
                report.shell_defview = self._find_child(
                    report.workerw_with_defview.hwnd,
                    "SHELLDLL_DefView",
                )

        if report.shell_defview:
            report.sys_listview = self._find_child(report.shell_defview.hwnd, "SysListView32")

        report.workerw_after_defview = self._find_workerw_after_defview(report)
        report.wallpaper_workerw = self._find_wallpaper_workerw(report)
        if report.workerw_after_defview:
            report.wallpaper_workerw = report.workerw_after_defview
        return report

    def request_workerw(self) -> list[tuple[int, int, bool, int]]:
        progman = win32gui.FindWindow("Progman", "Program Manager")
        if not progman:
            return []

        messages = [(0, 0), (0xD, 0), (0xD, 1), (0, 0)]
        results: list[tuple[int, int, bool, int]] = []

        for wparam, lparam in messages:
            result = ctypes.c_ulong()
            ok = ctypes.windll.user32.SendMessageTimeoutW(
                progman,
                SHELL_SPAWN_WORKERW,
                wparam,
                lparam,
                win32con.SMTO_NORMAL,
                1000,
                ctypes.byref(result),
            )
            results.append((wparam, lparam, bool(ok), int(result.value)))

        return results

    def _get_progman(self) -> WindowInfo | None:
        hwnd = win32gui.FindWindow("Progman", "Program Manager")
        return self._window_info(hwnd) if hwnd else None

    def _find_top_level_by_class(self, class_name: str) -> list[WindowInfo]:
        matches: list[WindowInfo] = []

        def callback(hwnd: int, _) -> bool:
            if _safe_class_name(hwnd) == class_name:
                info = self._window_info(hwnd)
                if info:
                    matches.append(info)
            return True

        win32gui.EnumWindows(callback, None)
        return matches

    def _find_workerw_with_defview(self, workerws: list[WindowInfo]) -> WindowInfo | None:
        for workerw in workerws:
            if self._find_child(workerw.hwnd, "SHELLDLL_DefView"):
                return workerw
        return None

    def _find_wallpaper_workerw(self, report: DesktopReport) -> WindowInfo | None:
        explorer_pid = report.progman.pid if report.progman else None
        candidates: list[WindowInfo] = []
        for workerw in report.workerws:
            if self._find_child(workerw.hwnd, "SHELLDLL_DefView"):
                continue

            area = _area(workerw)
            if explorer_pid is not None and workerw.pid != explorer_pid:
                report.rejected_workerws.append(
                    f"hwnd={workerw.hwnd} rejected: pid {workerw.pid} != explorer pid {explorer_pid}"
                )
                continue

            if area < 200_000:
                report.rejected_workerws.append(
                    f"hwnd={workerw.hwnd} rejected: area {area} is too small ({workerw.size})"
                )
                continue

            candidates.append(workerw)

        if not candidates:
            return None

        candidates.sort(key=_host_score, reverse=True)
        return candidates[0]

    def _find_workerw_after_defview(self, report: DesktopReport) -> WindowInfo | None:
        if (
            report.progman
            and report.shell_defview
            and report.shell_defview.parent == report.progman.hwnd
        ):
            hwnd = win32gui.FindWindowEx(
                report.progman.hwnd,
                report.shell_defview.hwnd,
                "WorkerW",
                None,
            )
            while hwnd:
                info = self._window_info(hwnd)
                if (
                    info
                    and info.pid == report.progman.pid
                    and _area(info) >= 200_000
                    and self._find_child(hwnd, "SHELLDLL_DefView") is None
                ):
                    return info
                hwnd = win32gui.FindWindowEx(report.progman.hwnd, hwnd, "WorkerW", None)

        defview_owner = report.workerw_with_defview or report.progman
        if not defview_owner:
            return None

        hwnd = win32gui.FindWindowEx(0, defview_owner.hwnd, "WorkerW", None)
        while hwnd:
            if self._find_child(hwnd, "SHELLDLL_DefView") is None:
                return self._window_info(hwnd)
            hwnd = win32gui.FindWindowEx(0, hwnd, "WorkerW", None)

        return None

    def _find_child(self, parent: int, class_name: str) -> WindowInfo | None:
        if not parent:
            return None

        found = win32gui.FindWindowEx(parent, 0, class_name, None)
        if found:
            return self._window_info(found)

        match: int | None = None

        def callback(hwnd: int, _) -> bool:
            nonlocal match
            if _safe_class_name(hwnd) == class_name:
                match = hwnd
                return False
            return True

        try:
            win32gui.EnumChildWindows(parent, callback, None)
        except win32gui.error:
            return None

        return self._window_info(match) if match else None

    def _window_info(self, hwnd: int | None) -> WindowInfo | None:
        if not hwnd or not win32gui.IsWindow(hwnd):
            return None

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return WindowInfo(
            hwnd=hwnd,
            class_name=_safe_class_name(hwnd),
            title=_safe_title(hwnd),
            parent=win32gui.GetParent(hwnd),
            pid=pid,
            visible=bool(win32gui.IsWindowVisible(hwnd)),
            rect=win32gui.GetWindowRect(hwnd),
        )


def enum_descendants(parent: int, predicate: Callable[[int], bool]) -> list[int]:
    matches: list[int] = []

    def callback(hwnd: int, _) -> bool:
        if predicate(hwnd):
            matches.append(hwnd)
        return True

    win32gui.EnumChildWindows(parent, callback, None)
    return matches


def _safe_class_name(hwnd: int) -> str:
    try:
        return win32gui.GetClassName(hwnd)
    except win32gui.error:
        return ""


def _safe_title(hwnd: int) -> str:
    try:
        return win32gui.GetWindowText(hwnd)
    except win32gui.error:
        return ""


def _format_window(label: str, info: WindowInfo | None) -> str:
    return f"{label}: {_window_summary(info)}"


def _window_summary(info: WindowInfo | None) -> str:
    if info is None:
        return "not found"

    return (
        f"hwnd={info.hwnd} class={info.class_name} title={info.title!r} "
        f"parent={info.parent} pid={info.pid} visible={info.visible} "
        f"rect={info.rect} size={info.size}"
    )


def _host_score(info: WindowInfo) -> tuple[int, int]:
    return int(info.visible), _area(info)


def _area(info: WindowInfo) -> int:
    left, top, right, bottom = info.rect
    return max(0, right - left) * max(0, bottom - top)
