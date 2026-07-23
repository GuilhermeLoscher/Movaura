from __future__ import annotations

import ctypes
import time
from collections import deque
from ctypes import wintypes
from dataclasses import dataclass


PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010


class FILETIME(ctypes.Structure):
    _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    def value(self) -> int:
        return (self.high << 32) | self.low


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


@dataclass(frozen=True)
class PerformanceSnapshot:
    processes: int = 0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    average_cpu_percent: float = 0.0
    peak_cpu_percent: float = 0.0
    average_memory_mb: float = 0.0

    def to_text(self) -> str:
        return (
            f"{self.processes} compositor(es) | CPU {self.cpu_percent:.1f}% | "
            f"RAM {self.memory_mb:.1f} MB | média {self.average_cpu_percent:.1f}%"
        )

    def detailed_text(self) -> str:
        return (
            f"{self.processes} compositor(es) | CPU atual {self.cpu_percent:.1f}% | "
            f"média {self.average_cpu_percent:.1f}% | pico {self.peak_cpu_percent:.1f}% | "
            f"RAM atual {self.memory_mb:.1f} MB | média {self.average_memory_mb:.1f} MB"
        )


class PerformanceMonitor:
    def __init__(self) -> None:
        self._last_at = time.monotonic()
        self._last_cpu: dict[int, int] = {}
        self._cpu_history: deque[float] = deque(maxlen=20)
        self._memory_history: deque[float] = deque(maxlen=20)

    def sample(self, process_ids: set[int]) -> PerformanceSnapshot:
        now = time.monotonic()
        elapsed = max(0.001, now - self._last_at)
        active_cpu: dict[int, int] = {}
        total_delta = 0
        memory_bytes = 0
        processes = 0
        for pid in process_ids:
            cpu_time, working_set = self._read_process(pid)
            if cpu_time is None:
                continue
            processes += 1
            active_cpu[pid] = cpu_time
            memory_bytes += working_set
            previous = self._last_cpu.get(pid)
            if previous is not None:
                total_delta += max(0, cpu_time - previous)
        self._last_at = now
        self._last_cpu = active_cpu
        cpu_percent = total_delta / 10_000_000 / elapsed * 100.0
        memory_mb = memory_bytes / 1024 / 1024
        self._cpu_history.append(cpu_percent)
        self._memory_history.append(memory_mb)
        return PerformanceSnapshot(
            processes=processes,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            average_cpu_percent=sum(self._cpu_history) / len(self._cpu_history),
            peak_cpu_percent=max(self._cpu_history),
            average_memory_mb=sum(self._memory_history) / len(self._memory_history),
        )

    @staticmethod
    def _read_process(pid: int) -> tuple[int | None, int]:
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        handle = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ,
            False,
            pid,
        )
        if not handle:
            return None, 0
        try:
            creation = FILETIME()
            exit_time = FILETIME()
            kernel = FILETIME()
            user = FILETIME()
            if not kernel32.GetProcessTimes(
                handle,
                ctypes.byref(creation),
                ctypes.byref(exit_time),
                ctypes.byref(kernel),
                ctypes.byref(user),
            ):
                return None, 0
            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            working_set = 0
            if psapi.GetProcessMemoryInfo(
                handle,
                ctypes.byref(counters),
                counters.cb,
            ):
                working_set = counters.WorkingSetSize
            return kernel.value() + user.value(), working_set
        finally:
            kernel32.CloseHandle(handle)
