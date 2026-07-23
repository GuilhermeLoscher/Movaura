"""Movaura support diagnostics. Desenvolvido por Guilherme Loscher (GL)."""

from __future__ import annotations

import json
import platform
from datetime import datetime
from pathlib import Path

from core.app_logging import log_path
from core.desktop_probe import DesktopProbe
from core.native_compositor import NativeCompositorLauncher
from core.native_host import NativeHost
from core.runtime_paths import data_root
from core.settings import MovauraSettings
from core.version import APP_AUTHOR_SIGNATURE, APP_VERSION
from core.wallpaper_library import WallpaperLibrary
from core.playlist_manager import PlaylistManager
from core.app_rule_manager import AppRuleManager
from core.monitor_profile_manager import MonitorProfileManager
from core.gpu_info import active_display_adapters
from core.benchmark import environment_text


LOG_TAIL_LINES = 180


def create_support_report(settings: MovauraSettings) -> Path:
    support_dir = data_root() / "support"
    support_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = support_dir / f"movaura-diagnostico-{timestamp}.txt"
    sections = [
        "MOVAURA - RELATÓRIO DE DIAGNÓSTICO",
        f"Gerado em: {datetime.now().isoformat(timespec='seconds')}",
        f"Versão: {APP_VERSION}",
        f"Autoria: {APP_AUTHOR_SIGNATURE}",
        f"Windows: {platform.platform()}",
        f"GPUs ativas: {', '.join(active_display_adapters()) or 'nao identificadas'}",
        environment_text(),
        "",
        "CONFIGURAÇÕES",
        json.dumps(settings.data, indent=2, sort_keys=True, ensure_ascii=False),
        "",
        "COMPOSITOR NATIVO",
        f"Executável: {NativeCompositorLauncher.default_executable()}",
        f"Existe: {NativeCompositorLauncher.default_executable().exists()}",
        "Aceleração de vídeo: Media Foundation solicita transformações de hardware quando disponíveis.",
        "",
        "BIBLIOTECA",
        json.dumps(WallpaperLibrary().stats(), indent=2, sort_keys=True),
        "",
        "AUTOMAÇÃO",
        f"Playlists: {', '.join(PlaylistManager().names())}",
        f"Regras por aplicativo: {len(AppRuleManager().rules())}",
        f"Perfis por monitor: {len(MonitorProfileManager().profiles())}",
        "",
        "EXPLORER / DESKTOP",
        _desktop_report(),
        "",
        "HOST NATIVO",
        _native_host_report(),
        "",
        "FINAL DO LOG",
        _log_tail(),
        "",
        "RELATORIOS DE FALHA",
        _crash_reports(),
    ]
    path.write_text("\n".join(sections), encoding="utf-8")
    return path


def _desktop_report() -> str:
    try:
        return DesktopProbe().probe(refresh_workerw=True).to_text()
    except Exception as exc:
        return f"Falha ao consultar Explorer: {type(exc).__name__}: {exc}"


def _native_host_report() -> str:
    try:
        return NativeHost().probe_text()
    except Exception as exc:
        return f"Falha ao consultar host nativo: {type(exc).__name__}: {exc}"


def _log_tail() -> str:
    path = log_path()
    if not path.exists():
        return "Log ainda não existe."
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return f"Falha ao ler log: {exc}"
    return "\n".join(lines[-LOG_TAIL_LINES:])


def _crash_reports() -> str:
    directory = data_root() / "crashes"
    if not directory.exists():
        return "Nenhuma falha registrada."
    reports = sorted(directory.glob("movaura-crash-*.txt"), reverse=True)[:5]
    return "\n".join(str(path) for path in reports) or "Nenhuma falha registrada."
