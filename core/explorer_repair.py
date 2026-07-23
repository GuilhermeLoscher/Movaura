from __future__ import annotations

import subprocess
import time

from core.desktop_probe import DesktopProbe, DesktopReport


class ExplorerHostRepair:
    def __init__(self, probe: DesktopProbe | None = None) -> None:
        self.probe = probe or DesktopProbe()

    def restart_explorer_and_probe(self, wait_seconds: float = 4.0) -> DesktopReport:
        print("Restarting Explorer to rebuild desktop host windows...")
        subprocess.run(
            ["taskkill", "/f", "/im", "explorer.exe"],
            check=False,
            capture_output=True,
            text=True,
        )
        time.sleep(1.0)
        subprocess.Popen(["explorer.exe"])
        time.sleep(wait_seconds)
        return self.probe.probe(refresh_workerw=True)

    def hide_forced_workerws(self) -> DesktopReport:
        import win32con
        import win32gui

        report = self.probe.probe(refresh_workerw=False)
        explorer_pid = report.progman.pid if report.progman else None
        if explorer_pid is None:
            return report

        for workerw in report.workerws:
            if workerw.pid != explorer_pid:
                continue

            left, top, right, bottom = workerw.rect
            area = max(0, right - left) * max(0, bottom - top)
            if area >= 200_000:
                print(f"Hiding forced WorkerW hwnd={workerw.hwnd} rect={workerw.rect}")
                win32gui.ShowWindow(workerw.hwnd, win32con.SW_HIDE)
                win32gui.MoveWindow(workerw.hwnd, 0, 0, 136, 39, True)

        return self.probe.probe(refresh_workerw=True)
