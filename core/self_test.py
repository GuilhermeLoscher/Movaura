from __future__ import annotations

from dataclasses import dataclass

from core.native_compositor import NativeCompositorLauncher
from core.native_host import NativeHost
from core.runtime_paths import app_root
from core.wallpaper_library import WallpaperLibrary
from core.playlist_manager import PlaylistManager
from core.app_rule_manager import AppRuleManager
from core.monitor_profile_manager import MonitorProfileManager
from core.performance_monitor import PerformanceMonitor
from core.scene_package import ScenePackageManager
from core.version import APP_VERSION
from core.gpu_info import active_display_adapters
from core.scene_presets import ScenePresetManager
from core.benchmark import environment_text


@dataclass(frozen=True)
class SelfTestResult:
    success: bool
    lines: list[str]

    def to_text(self) -> str:
        status = "APROVADO" if self.success else "FALHOU"
        return "\n".join([f"MOVAURA {APP_VERSION} - AUTOTESTE: {status}", *self.lines])


def run_self_test() -> SelfTestResult:
    lines: list[str] = []
    failures: list[str] = []
    stats = WallpaperLibrary().stats()
    lines.append(
        "Biblioteca: "
        f"{stats['images']} imagens, {stats['gifs']} GIFs, {stats['videos']} videos, "
        f"{stats['personal']} importados."
    )
    if stats["images"] < 20 or stats["gifs"] < 20 or stats["videos"] < 20:
        lines.append(
            "AVISO: biblioteca incluida reduzida ou ausente. "
            "Isto e esperado no instalador compacto; use a importacao de arquivos ou pastas."
        )

    compositor = NativeCompositorLauncher.default_executable()
    lines.append(f"Compositor nativo: {compositor} | existe={compositor.exists()}")
    if not compositor.exists():
        failures.append("O compositor nativo nao foi encontrado.")

    try:
        native_probe = NativeHost().probe_text()
        probe_ok = "probe_ok: True" in native_probe or "probe_ok: true" in native_probe
        lines.append(f"Host nativo: probe_ok={probe_ok}")
        if not probe_ok:
            lines.append(
                "AVISO: Explorer nao publicou uma arvore classica da area de trabalho nesta sessao. "
                "O compositor tentara reconstruir o host ao iniciar."
            )
    except Exception as exc:
        failures.append(f"Falha ao consultar host nativo: {exc}")

    lines.append(f"Pasta do aplicativo: {app_root()}")
    lines.append(f"GPUs ativas: {', '.join(active_display_adapters()) or 'nao identificadas'}.")
    lines.append(environment_text().replace("\n", " | "))
    lines.append(f"Playlists: {len(PlaylistManager().names())} configurada(s).")
    lines.append(f"Regras por aplicativo: {len(AppRuleManager().rules())}.")
    lines.append(f"Perfis por monitor: {len(MonitorProfileManager().profiles())}.")
    try:
        snapshot = PerformanceMonitor().sample(set())
        lines.append(f"Monitor de desempenho: {snapshot.to_text()}.")
    except Exception as exc:
        failures.append(f"Falha ao inicializar monitor de desempenho: {exc}")
    try:
        ScenePackageManager()
        lines.append("Pacotes de cena: disponiveis.")
    except Exception as exc:
        failures.append(f"Falha ao inicializar pacotes de cena: {exc}")
    try:
        lines.append(f"Presets pessoais: {len(ScenePresetManager().names())}.")
    except Exception as exc:
        failures.append(f"Falha ao consultar presets pessoais: {exc}")
    lines.extend(f"ERRO: {failure}" for failure in failures)
    return SelfTestResult(not failures, lines)
