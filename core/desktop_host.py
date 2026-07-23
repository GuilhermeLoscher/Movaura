from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import win32con
import win32gui

from core.desktop_probe import DesktopProbe, DesktopReport
from core.window_styles import (
    place_child,
    place_child_after,
    place_child_front,
    place_clickthrough_desktop_overlay,
    place_clickthrough_overlay_top,
    place_desktop_overlay,
    place_overlay,
    describe_clickthrough_z_order,
)


class HostMode(str, Enum):
    AUTO = "auto"
    SYSTEM_WALLPAPER = "system-wallpaper"
    NATIVE_COMPOSITION = "native-composition"
    NATIVE_WORKERW = "native-workerw"
    NATIVE_PROGMAN_STACK = "native-progman-stack"
    WORKERW = "workerw"
    WORKERW_FRONT = "workerw-front"
    WORKERW_FORCE = "workerw-force"
    WORKERW_FORCE_BOTTOM = "workerw-force-bottom"
    PROGMAN = "progman"
    PROGMAN_FRONT = "progman-front"
    DEFVIEW = "defview"
    DEFVIEW_UNDER_ICONS = "defview-under-icons"
    DEFVIEW_TRANSPARENT_ICONS = "defview-transparent-icons"
    LISTVIEW = "listview"
    DESKTOP_OVERLAY = "desktop-overlay"
    DESKTOP_CLICKTHROUGH = "desktop-clickthrough"
    DESKTOP_CLICKTHROUGH_TOP = "desktop-clickthrough-top"
    OVERLAY = "overlay"


CONTROL_PANEL_HOST_MODES = (
    HostMode.AUTO,
    HostMode.SYSTEM_WALLPAPER,
    HostMode.NATIVE_COMPOSITION,
)


@dataclass
class AttachResult:
    requested_mode: HostMode
    active_mode: HostMode
    success: bool
    parent_hwnd: int
    reason: str
    report: DesktopReport
    should_keep_window: bool = True

    def to_text(self) -> str:
        return (
            "Movaura host result:\n"
            f"  requested_mode: {self.requested_mode.value}\n"
            f"  active_mode: {self.active_mode.value}\n"
            f"  success: {self.success}\n"
            f"  parent_hwnd: {self.parent_hwnd}\n"
            f"  reason: {self.reason}"
        )


class DesktopHost:
    def __init__(self, probe: DesktopProbe | None = None) -> None:
        self.probe = probe or DesktopProbe()
        self._transparent_listview: int | None = None
        self._listview_background: int | None = None
        self._listview_text_background: int | None = None

    def attach(
        self,
        hwnd: int,
        mode: HostMode,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> AttachResult:
        report = self.probe.probe(refresh_workerw=True)

        if mode == HostMode.AUTO:
            for candidate in (HostMode.WORKERW, HostMode.PROGMAN):
                result = self._attach_mode(hwnd, candidate, x, y, width, height, report)
                if result.success:
                    return AttachResult(
                        requested_mode=mode,
                        active_mode=result.active_mode,
                        success=True,
                        parent_hwnd=result.parent_hwnd,
                        reason=result.reason,
                        report=report,
                    )
            return AttachResult(
                mode,
                HostMode.AUTO,
                False,
                0,
                f"auto mode refused an unsafe desktop host; {report.host_capability}",
                report,
                should_keep_window=False,
            )

        return self._attach_mode(hwnd, mode, x, y, width, height, report)

    def _attach_mode(
        self,
        hwnd: int,
        mode: HostMode,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        try:
            if mode == HostMode.NATIVE_WORKERW:
                return self._attach_native_workerw(hwnd, x, y, width, height, report)
            if mode == HostMode.NATIVE_PROGMAN_STACK:
                return self._attach_native_progman_stack(hwnd, x, y, width, height, report)
            if mode == HostMode.WORKERW:
                return self._attach_workerw(hwnd, x, y, width, height, report)
            if mode == HostMode.WORKERW_FRONT:
                return self._attach_workerw_front(hwnd, x, y, width, height, report)
            if mode == HostMode.WORKERW_FORCE:
                return self._attach_workerw_force(hwnd, x, y, width, height, report, keep_bottom=False)
            if mode == HostMode.WORKERW_FORCE_BOTTOM:
                return self._attach_workerw_force(hwnd, x, y, width, height, report, keep_bottom=True)
            if mode == HostMode.PROGMAN:
                return self._attach_progman(hwnd, x, y, width, height, report)
            if mode == HostMode.PROGMAN_FRONT:
                return self._attach_progman_front(hwnd, x, y, width, height, report)
            if mode == HostMode.DEFVIEW:
                return self._attach_defview(hwnd, x, y, width, height, report)
            if mode == HostMode.DEFVIEW_UNDER_ICONS:
                return self._attach_defview_under_icons(hwnd, x, y, width, height, report)
            if mode == HostMode.DEFVIEW_TRANSPARENT_ICONS:
                return self._attach_defview_transparent_icons(hwnd, x, y, width, height, report)
            if mode == HostMode.LISTVIEW:
                return self._attach_listview(hwnd, x, y, width, height, report)
            if mode == HostMode.DESKTOP_OVERLAY:
                return self._attach_desktop_overlay(hwnd, x, y, width, height, report)
            if mode == HostMode.DESKTOP_CLICKTHROUGH:
                return self._attach_desktop_clickthrough(hwnd, x, y, width, height, report)
            if mode == HostMode.DESKTOP_CLICKTHROUGH_TOP:
                return self._attach_desktop_clickthrough_top(hwnd, x, y, width, height, report)
            if mode == HostMode.OVERLAY:
                return self._attach_overlay(hwnd, x, y, width, height, report)
        except Exception as exc:
            return AttachResult(mode, mode, False, 0, f"{type(exc).__name__}: {exc}", report)

        return AttachResult(mode, mode, False, 0, f"unsupported mode: {mode}", report)

    def _attach_native_workerw(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        from core.native_host import NativeHost

        native = NativeHost()
        if not native.status.loaded:
            return AttachResult(
                HostMode.NATIVE_WORKERW,
                HostMode.NATIVE_WORKERW,
                False,
                0,
                native.status.message,
                report,
                should_keep_window=False,
            )

        result = native.attach_to_workerw_after_defview(hwnd, x, y, width, height)
        if result is None:
            return AttachResult(
                HostMode.NATIVE_WORKERW,
                HostMode.NATIVE_WORKERW,
                False,
                0,
                "native attach did not return a result",
                report,
                should_keep_window=False,
            )

        return AttachResult(
            HostMode.NATIVE_WORKERW,
            HostMode.NATIVE_WORKERW,
            bool(result.success),
            int(result.parent_hwnd),
            (
                "native attach to WorkerW-after-DefView succeeded"
                if result.success
                else f"native attach failed; last_error={result.last_error}"
            ),
            report,
            should_keep_window=bool(result.success),
        )

    def _attach_workerw(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        workerw = report.workerw_after_defview
        if not workerw:
            return AttachResult(
                HostMode.WORKERW,
                HostMode.WORKERW,
                False,
                0,
                "no safe WorkerW-after-DefView wallpaper host was found",
                report,
            )
        if workerw.parent:
            return AttachResult(
                HostMode.WORKERW,
                HostMode.WORKERW,
                False,
                workerw.hwnd,
                "WorkerW is nested under Progman; attach succeeds but Explorer paints an opaque layer above it",
                report,
                should_keep_window=False,
            )

        child_x, child_y = self._relative_to_parent(workerw.hwnd, x, y)
        place_child(hwnd, workerw.hwnd, child_x, child_y, width, height)
        self._send_behind_icons(hwnd)
        attached = self._is_attached(hwnd, workerw.hwnd)
        return AttachResult(
            HostMode.WORKERW,
            HostMode.WORKERW,
            attached,
            workerw.hwnd,
            "attached to validated wallpaper WorkerW" if attached else "SetParent to WorkerW failed",
            report,
        )

    def _attach_native_progman_stack(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        from core.native_host import NativeHost

        native = NativeHost()
        if not native.status.loaded:
            return AttachResult(
                HostMode.NATIVE_PROGMAN_STACK,
                HostMode.NATIVE_PROGMAN_STACK,
                False,
                0,
                native.status.message,
                report,
                should_keep_window=False,
            )

        result = native.attach_to_progman_stack(hwnd, x, y, width, height)
        if result is None:
            return AttachResult(
                HostMode.NATIVE_PROGMAN_STACK,
                HostMode.NATIVE_PROGMAN_STACK,
                False,
                0,
                "native Progman stack attach did not return a result",
                report,
                should_keep_window=False,
            )

        return AttachResult(
            HostMode.NATIVE_PROGMAN_STACK,
            HostMode.NATIVE_PROGMAN_STACK,
            bool(result.success),
            int(result.parent_hwnd),
            (
                "native attach below Progman icon layer succeeded"
                if result.success
                else f"native Progman stack attach failed; last_error={result.last_error}"
            ),
            report,
            should_keep_window=bool(result.success),
        )

    def _attach_workerw_front(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        workerw = report.workerw_after_defview
        if not workerw:
            return AttachResult(
                HostMode.WORKERW_FRONT,
                HostMode.WORKERW_FRONT,
                False,
                0,
                "no WorkerW-after-DefView host was found",
                report,
                should_keep_window=False,
            )

        child_x, child_y = self._relative_to_parent(workerw.hwnd, x, y)
        place_child_front(hwnd, workerw.hwnd, child_x, child_y, width, height)
        attached = self._is_attached(hwnd, workerw.hwnd)
        return AttachResult(
            HostMode.WORKERW_FRONT,
            HostMode.WORKERW_FRONT,
            attached,
            workerw.hwnd,
            (
                "diagnostic: attached as top child of WorkerW desktop host"
                if attached
                else "SetParent to WorkerW failed"
            ),
            report,
            should_keep_window=attached,
        )

    def _attach_workerw_force(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
        keep_bottom: bool,
    ) -> AttachResult:
        workerw = self._find_forceable_workerw(report)
        if not workerw:
            return AttachResult(
                HostMode.WORKERW_FORCE_BOTTOM if keep_bottom else HostMode.WORKERW_FORCE,
                HostMode.WORKERW_FORCE_BOTTOM if keep_bottom else HostMode.WORKERW_FORCE,
                False,
                0,
                "no Explorer-owned WorkerW candidate exists to force",
                report,
            )

        win32gui.ShowWindow(workerw.hwnd, win32con.SW_SHOW)
        win32gui.MoveWindow(workerw.hwnd, x, y, width, height, True)
        win32gui.SetWindowPos(
            workerw.hwnd,
            win32con.HWND_BOTTOM if keep_bottom else win32con.HWND_TOP,
            x,
            y,
            width,
            height,
            win32con.SWP_SHOWWINDOW | win32con.SWP_NOACTIVATE,
        )

        place_child(hwnd, workerw.hwnd, 0, 0, width, height)
        self._send_behind_icons(hwnd)
        attached = self._is_attached(hwnd, workerw.hwnd)
        return AttachResult(
            HostMode.WORKERW_FORCE_BOTTOM if keep_bottom else HostMode.WORKERW_FORCE,
            HostMode.WORKERW_FORCE_BOTTOM if keep_bottom else HostMode.WORKERW_FORCE,
            attached,
            workerw.hwnd,
            (
                "experimental: resized an Explorer WorkerW candidate to the monitor"
                if attached
                else "experimental WorkerW force failed"
            ),
            report,
        )

    def _attach_progman(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        if report.progman:
            parent = report.progman.hwnd
            reason = "attached to Progman fallback"
        elif report.shell_defview:
            parent = report.shell_defview.hwnd
            reason = "attached to SHELLDLL_DefView fallback"
        else:
            return AttachResult(
                HostMode.PROGMAN,
                HostMode.PROGMAN,
                False,
                0,
                "Progman was not found",
                report,
            )

        child_x, child_y = self._relative_to_parent(parent, x, y)
        place_child(hwnd, parent, child_x, child_y, width, height)
        self._send_behind_icons(hwnd)
        attached = self._is_attached(hwnd, parent)
        if attached and report.shell_defview and report.shell_defview.parent == parent:
            return AttachResult(
                HostMode.PROGMAN,
                HostMode.PROGMAN,
                False,
                parent,
                "Progman contains SHELLDLL_DefView directly; bottom child is hidden behind icon layer",
                report,
                should_keep_window=False,
            )
        return AttachResult(
            HostMode.PROGMAN,
            HostMode.PROGMAN,
            attached,
            parent,
            reason if attached else "SetParent to Progman/SHELLDLL failed",
            report,
        )

    def _attach_progman_front(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        if not report.progman:
            return AttachResult(
                HostMode.PROGMAN_FRONT,
                HostMode.PROGMAN_FRONT,
                False,
                0,
                "Progman was not found",
                report,
            )

        child_x, child_y = self._relative_to_parent(report.progman.hwnd, x, y)
        place_child_front(hwnd, report.progman.hwnd, child_x, child_y, width, height)
        attached = self._is_attached(hwnd, report.progman.hwnd)
        return AttachResult(
            HostMode.PROGMAN_FRONT,
            HostMode.PROGMAN_FRONT,
            attached,
            report.progman.hwnd,
            "diagnostic: attached above Progman children; may cover desktop icons",
            report,
        )

    def _attach_defview(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        if not report.shell_defview:
            return AttachResult(
                HostMode.DEFVIEW,
                HostMode.DEFVIEW,
                False,
                0,
                "SHELLDLL_DefView was not found",
                report,
            )

        child_x, child_y = self._relative_to_parent(report.shell_defview.hwnd, x, y)
        place_child(hwnd, report.shell_defview.hwnd, child_x, child_y, width, height)
        self._send_behind_icons(hwnd)
        attached = self._is_attached(hwnd, report.shell_defview.hwnd)
        return AttachResult(
            HostMode.DEFVIEW,
            HostMode.DEFVIEW,
            attached,
            report.shell_defview.hwnd,
            "diagnostic: attached as bottom child of SHELLDLL_DefView",
            report,
        )

    def _attach_listview(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        if not report.sys_listview:
            return AttachResult(
                HostMode.LISTVIEW,
                HostMode.LISTVIEW,
                False,
                0,
                "SysListView32 was not found",
                report,
            )

        child_x, child_y = self._relative_to_parent(report.sys_listview.hwnd, x, y)
        place_child(hwnd, report.sys_listview.hwnd, child_x, child_y, width, height)
        self._send_behind_icons(hwnd)
        attached = self._is_attached(hwnd, report.sys_listview.hwnd)
        return AttachResult(
            HostMode.LISTVIEW,
            HostMode.LISTVIEW,
            attached,
            report.sys_listview.hwnd,
            "diagnostic: attached as bottom child of SysListView32",
            report,
        )

    def _attach_defview_under_icons(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        if not report.shell_defview:
            return AttachResult(
                HostMode.DEFVIEW_UNDER_ICONS,
                HostMode.DEFVIEW_UNDER_ICONS,
                False,
                0,
                "SHELLDLL_DefView was not found",
                report,
            )
        if not report.sys_listview:
            return AttachResult(
                HostMode.DEFVIEW_UNDER_ICONS,
                HostMode.DEFVIEW_UNDER_ICONS,
                False,
                0,
                "SysListView32 was not found",
                report,
            )

        child_x, child_y = self._relative_to_parent(report.shell_defview.hwnd, x, y)
        place_child_after(
            hwnd,
            report.shell_defview.hwnd,
            report.sys_listview.hwnd,
            child_x,
            child_y,
            width,
            height,
        )
        attached = self._is_attached(hwnd, report.shell_defview.hwnd)
        return AttachResult(
            HostMode.DEFVIEW_UNDER_ICONS,
            HostMode.DEFVIEW_UNDER_ICONS,
            attached,
            report.shell_defview.hwnd,
            "diagnostic: attached to SHELLDLL_DefView directly after SysListView32 in z-order",
            report,
        )

    def _attach_defview_transparent_icons(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        if not report.shell_defview or not report.sys_listview:
            return AttachResult(
                HostMode.DEFVIEW_TRANSPARENT_ICONS,
                HostMode.DEFVIEW_TRANSPARENT_ICONS,
                False,
                0,
                "SHELLDLL_DefView or SysListView32 was not found",
                report,
                should_keep_window=False,
            )

        self._enable_transparent_icons(report.sys_listview.hwnd)
        child_x, child_y = self._relative_to_parent(report.shell_defview.hwnd, x, y)
        place_child_after(
            hwnd,
            report.shell_defview.hwnd,
            report.sys_listview.hwnd,
            child_x,
            child_y,
            width,
            height,
        )
        attached = self._is_attached(hwnd, report.shell_defview.hwnd)
        if not attached:
            self.restore_desktop()
        return AttachResult(
            HostMode.DEFVIEW_TRANSPARENT_ICONS,
            HostMode.DEFVIEW_TRANSPARENT_ICONS,
            attached,
            report.shell_defview.hwnd,
            (
                "experimental: attached below transparent desktop icon ListView"
                if attached
                else "transparent icon-layer attach failed"
            ),
            report,
            should_keep_window=attached,
        )

    def restore_desktop(self) -> None:
        if not self._transparent_listview or not win32gui.IsWindow(self._transparent_listview):
            self._clear_transparent_icon_state()
            return

        if self._listview_background is not None:
            win32gui.SendMessage(self._transparent_listview, 0x1001, 0, self._listview_background)
        if self._listview_text_background is not None:
            win32gui.SendMessage(self._transparent_listview, 0x1026, 0, self._listview_text_background)
        win32gui.InvalidateRect(self._transparent_listview, None, True)
        self._clear_transparent_icon_state()

    def _enable_transparent_icons(self, listview: int) -> None:
        self.restore_desktop()
        self._transparent_listview = listview
        self._listview_background = win32gui.SendMessage(listview, 0x1000, 0, 0)
        self._listview_text_background = win32gui.SendMessage(listview, 0x1025, 0, 0)
        win32gui.SendMessage(listview, 0x1001, 0, 0xFFFFFFFF)
        win32gui.SendMessage(listview, 0x1026, 0, 0xFFFFFFFF)
        win32gui.InvalidateRect(listview, None, True)

    def _clear_transparent_icon_state(self) -> None:
        self._transparent_listview = None
        self._listview_background = None
        self._listview_text_background = None

    def _attach_overlay(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        place_overlay(hwnd, x, y, width, height)
        return AttachResult(
            HostMode.OVERLAY,
            HostMode.OVERLAY,
            True,
            0,
            "using explicit visible fullscreen overlay fallback",
            report,
        )

    def _attach_desktop_overlay(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        place_desktop_overlay(hwnd, x, y, width, height)
        return AttachResult(
            HostMode.DESKTOP_OVERLAY,
            HostMode.DESKTOP_OVERLAY,
            True,
            0,
            "using visible no-activate desktop overlay; covers desktop icons when no WorkerW exists",
            report,
        )

    def _attach_desktop_clickthrough(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        progman = report.progman.hwnd if report.progman else 0
        place_clickthrough_desktop_overlay(hwnd, progman, x, y, width, height)
        z_order = describe_clickthrough_z_order(hwnd, progman)
        return AttachResult(
            HostMode.DESKTOP_CLICKTHROUGH,
            HostMode.DESKTOP_CLICKTHROUGH,
            True,
            0,
            "experimental: click-through composition surface above desktop; "
            f"desktop icons are visually covered; {z_order}",
            report,
        )

    def _attach_desktop_clickthrough_top(
        self,
        hwnd: int,
        x: int,
        y: int,
        width: int,
        height: int,
        report: DesktopReport,
    ) -> AttachResult:
        progman = report.progman.hwnd if report.progman else 0
        place_clickthrough_overlay_top(hwnd, x, y, width, height)
        z_order = describe_clickthrough_z_order(hwnd, progman)
        return AttachResult(
            HostMode.DESKTOP_CLICKTHROUGH_TOP,
            HostMode.DESKTOP_CLICKTHROUGH_TOP,
            True,
            0,
            "diagnostic: click-through top non-topmost surface; "
            f"desktop icons are visually covered; {z_order}",
            report,
        )

    def _send_behind_icons(self, hwnd: int) -> None:
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_BOTTOM,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE
            | win32con.SWP_NOSIZE
            | win32con.SWP_NOACTIVATE
            | win32con.SWP_SHOWWINDOW,
        )

    def _is_attached(self, hwnd: int, parent: int) -> bool:
        return win32gui.IsWindow(hwnd) and win32gui.GetParent(hwnd) == parent

    def _relative_to_parent(self, parent: int, x: int, y: int) -> tuple[int, int]:
        left, top, _, _ = win32gui.GetWindowRect(parent)
        return x - left, y - top

    def _find_forceable_workerw(self, report: DesktopReport):
        explorer_pid = report.progman.pid if report.progman else None
        if explorer_pid is None:
            return None

        for workerw in report.workerws:
            if workerw.pid != explorer_pid:
                continue
            if workerw.hwnd == report.progman.hwnd:
                continue
            return workerw

        return None
