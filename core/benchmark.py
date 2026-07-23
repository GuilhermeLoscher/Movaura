from __future__ import annotations

import platform
import time
from dataclasses import dataclass

from core.gpu_info import active_display_adapters
from core.performance_monitor import PerformanceMonitor


@dataclass(frozen=True)
class BenchmarkResult:
    profile: str
    average_cpu_percent: float
    peak_cpu_percent: float
    average_memory_mb: float
    duration_seconds: int

    def to_text(self) -> str:
        labels = {"economy": "Leve", "adaptive": "Recomendado", "quality": "Maxima qualidade"}
        return (
            f"Perfil sugerido: {labels.get(self.profile, self.profile)}\n"
            f"CPU media: {self.average_cpu_percent:.1f}% | pico: {self.peak_cpu_percent:.1f}%\n"
            f"RAM media do compositor: {self.average_memory_mb:.1f} MB\n"
            f"Duracao: {self.duration_seconds}s"
        )


def run_benchmark(process_ids: set[int], duration_seconds: int = 30) -> BenchmarkResult:
    monitor = PerformanceMonitor()
    snapshots = []
    for _ in range(max(1, duration_seconds * 2)):
        snapshots.append(monitor.sample(process_ids))
        time.sleep(0.5)
    average_cpu = sum(item.cpu_percent for item in snapshots) / len(snapshots)
    peak_cpu = max(item.cpu_percent for item in snapshots)
    average_memory = sum(item.memory_mb for item in snapshots) / len(snapshots)
    if average_cpu >= 22 or peak_cpu >= 45:
        profile = "economy"
    elif average_cpu <= 8 and peak_cpu <= 20:
        profile = "quality"
    else:
        profile = "adaptive"
    return BenchmarkResult(profile, average_cpu, peak_cpu, average_memory, duration_seconds)


def environment_text() -> str:
    return (
        f"Windows: {platform.platform()}\n"
        f"GPUs: {', '.join(active_display_adapters()) or 'nao identificadas'}"
    )
