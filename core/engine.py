"""Movaura runtime orchestration. Desenvolvido por Guilherme Loscher (GL)."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QWidget

from core.desktop_host import DesktopHost, HostMode
from core.desktop_probe import DesktopProbe
from core.app_rule_manager import AppRuleManager
from core.fullscreen_detector import FullscreenAppDetector
from core.hotkey_manager import GlobalHotkeyManager
from core.monitor_manager import MonitorInfo, MonitorManager
from core.native_compositor import NativeCompositorLauncher
from core.plugin_manager import PluginManager
from core.playlist_manager import PlaylistManager
from core.performance_monitor import PerformanceMonitor, PerformanceSnapshot
from core.power_status import PowerStatusReader
from core.presentation_backend import PresentationBackend, PresentationPolicy
from core.settings import MovauraSettings
from core.session_state import SessionStateReader
from core.system_wallpaper import SystemWallpaperBackend
from core.telemetry import TelemetryClient
from core.tray import MovauraTray
from core.video_optimizer import VideoOptimizer
from core.wallpaper_window import WallpaperWindow
from renderers.factory import RendererFactory


class MovauraEngine:
    def __init__(
        self,
        app: QApplication,
        settings: MovauraSettings,
        diagnose: bool = False,
        quit_when_no_windows: bool = True,
    ) -> None:
        self.app = app
        self.settings = settings
        self.diagnose = diagnose
        self.quit_when_no_windows = quit_when_no_windows
        self.probe = DesktopProbe()
        self.host = DesktopHost(self.probe)
        self.monitors = MonitorManager()
        self.plugin_manager = PluginManager()
        self.power_status = PowerStatusReader()
        self.presentation_policy = PresentationPolicy()
        self.fullscreen_detector = FullscreenAppDetector()
        self.app_rules = AppRuleManager()
        self.playlists = PlaylistManager()
        self.performance_monitor = PerformanceMonitor()
        self.session_state = SessionStateReader()
        self.last_performance_snapshot = PerformanceSnapshot()
        self.telemetry = TelemetryClient(
            settings.get_bool("telemetry_enabled"),
            settings.get_str("telemetry_endpoint"),
        )
        self.video_optimizer = VideoOptimizer()
        self.native_compositor = NativeCompositorLauncher()
        self.last_backend: PresentationBackend | None = None
        self.windows: list[WallpaperWindow] = []
        self.tray: MovauraTray | None = None
        self.control_panel: QWidget | None = None
        self.status_callback: Callable[[str], None] | None = None
        self.presentation_callback: Callable[[dict[str, object]], None] | None = None
        self._native_paused = False
        self._native_monitors: list[MonitorInfo] = []
        self._auto_paused = False
        self._manually_paused = False
        self._rule_paused = False
        self._session_paused = False
        self._playlist_index = -1
        self._playlist_timer = QTimer()
        self._playlist_timer.setSingleShot(True)
        self._playlist_timer.timeout.connect(self.next_playlist_item)
        self._rule_timer = QTimer()
        self._rule_timer.setInterval(1500)
        self._rule_timer.timeout.connect(self._check_app_rules)
        self.hotkeys = GlobalHotkeyManager(
            {1: self.toggle_pause, 2: self.next_playlist_item, 3: self.restart}
        )
        self._fullscreen_timer = QTimer()
        self._fullscreen_timer.setInterval(1500)
        self._fullscreen_timer.timeout.connect(self._check_fullscreen_policy)
        self._power_timer = QTimer()
        self._power_timer.setInterval(5000)
        self._power_timer.timeout.connect(self._check_power_policy)
        self._health_timer = QTimer()
        self._health_timer.setInterval(3000)
        self._health_timer.timeout.connect(self._check_compositor_health)
        self._performance_timer = QTimer()
        self._performance_timer.setInterval(2500)
        self._performance_timer.timeout.connect(self._sample_performance)
        self._active_native_fps: int | None = None
        self._adaptive_fps_cap: int | None = None
        self._adaptive_cool_samples = 0
        self._auto_performance_samples = 0
        self._auto_performance_applied = False
        self._recovery_attempts = 0
        self._max_recovery_attempts = 10
        self._fullscreen_positive_samples = 0
        self._fullscreen_negative_samples = 0
        self.app.aboutToQuit.connect(self.stop)

    def start(self) -> None:
        report = self.probe.probe(refresh_workerw=self.diagnose)
        if self.diagnose:
            print(report.to_text())

        selected_monitors = self.monitors.select(self.settings.data.get("screen", "all"))
        if not selected_monitors:
            print("No monitors selected. Falling back to all monitors.")
            selected_monitors = self.monitors.monitors()
        for monitor in selected_monitors:
            print(f"MONITOR: {monitor.to_text()}")

        plugin_renderers = {}
        if self.settings.get_bool("plugins_enabled"):
            plugins = self.plugin_manager.discover()
            print(f"Plugins loaded: {len(plugins)}")
            plugin_renderers = self.plugin_manager.renderer_factories()

        renderer_factory = RendererFactory(plugin_renderers)
        try:
            host_mode = HostMode(self.settings.get_str("host_mode"))
        except ValueError:
            print("Invalid host_mode in settings. Falling back to auto.")
            host_mode = HostMode.AUTO

        decision = self.presentation_policy.decide(
            host_mode.value,
            report,
            renderer=self.settings.get_str("renderer"),
        )
        self.last_backend = decision.backend
        print(decision.to_text())
        if decision.backend == PresentationBackend.SYSTEM_WALLPAPER:
            result = SystemWallpaperBackend().apply(
                self.settings.get_str("renderer"),
                self.settings.get_str("color"),
                self.settings.get_str("media_path"),
                self.settings.get_str("wallpaper_position"),
            )
            print(f"Movaura system wallpaper: success={result.success} reason={result.message}")
            if result.path:
                print(f"  path: {result.path}")
            if self.quit_when_no_windows:
                self.app.quit()
            return
        if decision.backend == PresentationBackend.NATIVE_COMPOSITION:
            self._native_monitors = selected_monitors
            if self._start_native_compositor():
                self._start_fullscreen_policy()
                self._start_power_policy()
                self._health_timer.start()
                self._performance_timer.start()
                self._start_product_policies()
                if self.settings.get_bool("tray_enabled"):
                    self.tray = MovauraTray(self.app, self)
                    self.tray.show()
                    self._update_tray_state()
                print("MOVAURA 0.9.0 STARTED")
                self.telemetry.record("wallpaper_started", {"renderer": self.settings.get_str("renderer")})
                return
            if self.quit_when_no_windows:
                self.app.quit()
            return
        if decision.backend == PresentationBackend.BLOCKED:
            print("No wallpaper windows are active.")
            if self.quit_when_no_windows:
                self.app.quit()
            return

        for monitor in selected_monitors:
            self._start_monitor(monitor, renderer_factory, host_mode)

        if not self.windows:
            print("No wallpaper windows are active.")
            if self.quit_when_no_windows:
                self.app.quit()
            return

        if self.settings.get_bool("tray_enabled"):
            self.tray = MovauraTray(self.app, self)
            self.tray.show()

        print("MOVAURA 0.9.0 STARTED")

    def restart(self) -> None:
        self.stop()
        self.start()

    def reconfigure_native_compositor(self) -> bool:
        selected_monitors = self.monitors.select(self.settings.data.get("screen", "all"))
        if selected_monitors:
            self._native_monitors = selected_monitors
        return self._start_native_compositor()

    def set_control_panel(self, panel: QWidget) -> None:
        self.control_panel = panel

    def set_status_callback(self, callback: Callable[[str], None]) -> None:
        self.status_callback = callback

    def set_presentation_callback(self, callback: Callable[[dict[str, object]], None]) -> None:
        self.presentation_callback = callback

    def open_control_panel(self) -> None:
        if not self.control_panel:
            return
        self.control_panel.showNormal()
        self.control_panel.raise_()
        self.control_panel.activateWindow()

    def pause(self) -> None:
        if self.last_backend == PresentationBackend.NATIVE_COMPOSITION:
            self.native_compositor.stop()
            self._native_paused = True
            self._manually_paused = True
            self._auto_paused = False
            self._update_tray_state()
            self._report_status("Animação pausada manualmente.")
            return
        for window in self.windows:
            window.stop()

    def resume(self) -> None:
        if self.last_backend == PresentationBackend.NATIVE_COMPOSITION:
            if self._native_paused:
                if self._start_native_compositor():
                    self._manually_paused = False
                    self._auto_paused = False
                    self._recovery_attempts = 0
                    self._update_tray_state()
                    self._report_status("Animação retomada.")
            return
        for window in self.windows:
            window.start()

    def stop(self) -> None:
        self._fullscreen_timer.stop()
        self._power_timer.stop()
        self._health_timer.stop()
        self._performance_timer.stop()
        self._playlist_timer.stop()
        self._rule_timer.stop()
        self.hotkeys.stop()
        self.native_compositor.stop()
        self._active_native_fps = None
        self._adaptive_fps_cap = None
        self._adaptive_cool_samples = 0
        self._auto_performance_samples = 0
        self._auto_performance_applied = False
        self._recovery_attempts = 0
        self._native_paused = False
        self._auto_paused = False
        self._manually_paused = False
        self._rule_paused = False
        self._session_paused = False
        if self.tray:
            self.tray.tray.hide()
            self.tray = None
        while self.windows:
            window = self.windows.pop()
            window.stop()
            window.close()
        self.host.restore_desktop()

    def toggle_pause(self) -> None:
        if self._native_paused:
            self.resume()
        else:
            self.pause()

    def next_playlist_item(self) -> None:
        if not self.settings.get_bool("playlist_enabled"):
            return
        entries = self.playlists.entries(self.settings.get_str("active_playlist"))
        if not entries:
            self._report_status("A playlist ativa está vazia.")
            return
        self._playlist_index = (self._playlist_index + 1) % len(entries)
        entry = entries[self._playlist_index]
        presentation = self.playlists.presentation_for(entry)
        if not presentation:
            self._report_status("Um item inválido da playlist foi ignorado.")
            self._playlist_timer.start(1000)
            return
        self.settings.data.update(presentation)
        self.settings.save()
        if self.presentation_callback:
            self.presentation_callback(dict(presentation))
        if self.last_backend == PresentationBackend.NATIVE_COMPOSITION and not self._native_paused:
            self._start_native_compositor()
        self._playlist_timer.start(entry.duration_seconds * 1000)
        self._update_tray_state()
        self.telemetry.record("playlist_advanced", {"playlist": self.settings.get_str("active_playlist")})
        self._report_status(f"Playlist: {Path(entry.path).stem}.")

    def _start_native_compositor(self, pause_on_failure: bool = True) -> bool:
        fps = self._effective_native_fps()
        renderer = self.settings.get_str("renderer")
        media_path = self._native_media_path(renderer, self.settings.get_str("media_path"), fps)
        assignments = self._native_assignments(fps)
        results = self.native_compositor.launch_monitors(
            monitors=self._native_monitors,
            renderer=renderer,
            color=self.settings.get_str("color"),
            fps=fps,
            media_path=media_path,
            surface=self.settings.get_str("native_surface"),
            multi_monitor_mode=self.settings.get_str("multi_monitor_mode"),
            assignments=assignments,
            effect_intensity=self.settings.get_int("effect_intensity"),
            effect_speed=self.settings.get_int("effect_speed"),
        )
        for result in results:
            print(
                "Movaura native compositor: "
                f"success={result.success} reason={result.message}"
            )
            if result.path:
                print(f"  path: {result.path}")
        success = bool(results) and all(result.success for result in results)
        if not success:
            if not self.native_compositor.is_running:
                self.native_compositor.stop()
                self._active_native_fps = None
        else:
            self._active_native_fps = fps
        self._native_paused = not self.native_compositor.is_running and pause_on_failure
        return success

    def _native_media_path(self, renderer: str, media_path: str, fps: int) -> str:
        if renderer != "video" or not self.settings.get_bool("optimize_videos"):
            return media_path
        result = self.video_optimizer.optimize(
            media_path,
            self.settings.get_str("performance_profile"),
            fps,
            self.settings.get_str("multi_monitor_mode"),
        )
        if result.optimized:
            print(f"Movaura optimizer: {result.message}")
            self._report_status("Vídeo otimizado em cache para reduzir CPU.")
        else:
            print(f"Movaura optimizer: {result.message}")
        return result.path

    def _native_assignments(self, fps: int) -> dict[str, dict[str, str]]:
        assignments = self.settings.data.get("monitor_assignments", {})
        if not isinstance(assignments, dict):
            return {}
        if not self.settings.get_bool("optimize_videos"):
            return assignments
        optimized: dict[str, dict[str, str]] = {}
        for key, assignment in assignments.items():
            if not isinstance(assignment, dict):
                continue
            next_assignment = dict(assignment)
            renderer = str(next_assignment.get("renderer", self.settings.get_str("renderer")))
            media_path = str(next_assignment.get("media_path", self.settings.get_str("media_path")))
            next_assignment["media_path"] = self._native_media_path(renderer, media_path, fps)
            optimized[str(key)] = next_assignment
        return optimized

    def _start_fullscreen_policy(self) -> None:
        if self.settings.get_bool("pause_when_fullscreen_app"):
            self._fullscreen_timer.start()

    def _start_power_policy(self) -> None:
        self._power_timer.start()

    def _start_product_policies(self) -> None:
        if self.settings.get_bool("global_hotkeys_enabled"):
            self.hotkeys.start()
        if self.settings.get_bool("app_rules_enabled"):
            self._rule_timer.start()
        if self.settings.get_bool("playlist_enabled"):
            self._start_playlist_policy()

    def _start_playlist_policy(self) -> None:
        entries = self.playlists.entries(self.settings.get_str("active_playlist"))
        if not entries:
            self._report_status("A playlist ativa está vazia.")
            return
        current_media = str(Path(self.settings.get_str("media_path")).expanduser())
        for index, entry in enumerate(entries):
            if str(Path(entry.path).expanduser()) == current_media:
                self._playlist_index = index
                self._playlist_timer.start(entry.duration_seconds * 1000)
                return
        self.next_playlist_item()

    def _check_app_rules(self) -> None:
        if (
            self.last_backend != PresentationBackend.NATIVE_COMPOSITION
            or self._manually_paused
        ):
            return
        should_pause = self.app_rules.foreground_action() == "pause"
        if should_pause and not self._rule_paused:
            self.native_compositor.stop()
            self._native_paused = True
            self._rule_paused = True
            self._update_tray_state()
            self._report_status("Animação pausada por regra de aplicativo.")
        elif not should_pause and self._rule_paused and not self._session_paused:
            if self._start_native_compositor():
                self._rule_paused = False
                self._update_tray_state()
                self._report_status("Animação retomada após regra de aplicativo.")

    def _effective_native_fps(self) -> int:
        configured_fps = self.settings.get_int("fps")
        profile = self.settings.get_str("performance_profile")
        profile_cap = {
            "economy": 15,
            "balanced": 30,
            "quality": 60,
            "adaptive": 30,
        }.get(profile, configured_fps)
        configured_fps = min(configured_fps, profile_cap)
        if profile == "adaptive" and self._adaptive_fps_cap:
            configured_fps = min(configured_fps, self._adaptive_fps_cap)
        if (
            self.settings.get_bool("low_power_mode")
            and self.power_status.read().on_battery is True
        ):
            return min(configured_fps, 15)
        return configured_fps

    def _check_power_policy(self) -> None:
        if self.last_backend != PresentationBackend.NATIVE_COMPOSITION:
            return
        locked = self.session_state.is_locked()
        if locked and not (
            self._manually_paused
            or self._auto_paused
            or self._rule_paused
            or self._session_paused
        ):
            self.native_compositor.stop()
            self._native_paused = True
            self._session_paused = True
            self._update_tray_state()
            self._report_status("Animação pausada enquanto o Windows está bloqueado.")
            return
        if not locked and self._session_paused and not (
            self._manually_paused or self._auto_paused or self._rule_paused
        ):
            if self._start_native_compositor():
                self._session_paused = False
                self._update_tray_state()
                self._report_status("Animação retomada após desbloquear o Windows.")
            return
        if (
            self._native_paused
            or not self.native_compositor.is_running
        ):
            return
        fps = self._effective_native_fps()
        if fps == self._active_native_fps:
            return
        if self._start_native_compositor():
            if fps < self.settings.get_int("fps"):
                if self.settings.get_str("performance_profile") == "adaptive":
                    print("Movaura: perfil adaptativo reduziu o consumo do compositor.")
                    self._report_status("Perfil adaptativo: FPS reduzido para manter o sistema fluido.")
                    return
                print("Movaura: modo de baixo consumo ativado na bateria.")
                self._report_status("Modo de baixo consumo ativado: máximo de 15 FPS.")
            else:
                print("Movaura: FPS normal restaurado após conectar à tomada.")
                self._report_status("Tomada conectada: FPS configurado restaurado.")

    def _check_compositor_health(self) -> None:
        if (
            self.last_backend != PresentationBackend.NATIVE_COMPOSITION
            or self._native_paused
            or self.native_compositor.running_count == self.native_compositor.expected_count
        ):
            return
        self._recovery_attempts += 1
        print(
            "Movaura: compositor encerrou inesperadamente; "
            f"tentativa de recuperação {self._recovery_attempts}/"
            f"{self._max_recovery_attempts}."
        )
        self._report_status("O compositor encerrou inesperadamente. Tentando recuperar...")
        if self._start_native_compositor(pause_on_failure=False):
            self._recovery_attempts = 0
            print("Movaura: compositor recuperado automaticamente.")
            self._update_tray_state()
            self._report_status("Compositor recuperado automaticamente.")
            return
        if self._recovery_attempts >= self._max_recovery_attempts:
            self._native_paused = True
            print("Movaura: recuperação automática interrompida após dez tentativas.")
            self._update_tray_state()
            self._report_status("Não foi possível recuperar o compositor. Use Continuar ou Iniciar.")

    def _sample_performance(self) -> None:
        self.last_performance_snapshot = self.performance_monitor.sample(
            self.native_compositor.process_ids
        )
        self._check_intelligent_performance_policy()
        if self.settings.get_str("performance_profile") != "adaptive":
            self._adaptive_fps_cap = None
            self._adaptive_cool_samples = 0
            return
        average_cpu = self.last_performance_snapshot.average_cpu_percent
        next_cap = self._adaptive_fps_cap
        if average_cpu >= 20.0:
            next_cap = 15
            self._adaptive_cool_samples = 0
        elif average_cpu >= 12.0:
            next_cap = 20
            self._adaptive_cool_samples = 0
        elif next_cap is not None and average_cpu <= 6.0:
            self._adaptive_cool_samples += 1
            if self._adaptive_cool_samples >= 8:
                next_cap = 20 if next_cap < 20 else None
                self._adaptive_cool_samples = 0
        else:
            self._adaptive_cool_samples = 0
        if next_cap != self._adaptive_fps_cap:
            self._adaptive_fps_cap = next_cap
            self._check_power_policy()

    def _check_intelligent_performance_policy(self) -> None:
        if (
            not self.settings.get_bool("auto_performance_enabled")
            or self.last_backend != PresentationBackend.NATIVE_COMPOSITION
            or self._native_paused
            or not self.native_compositor.is_running
        ):
            self._auto_performance_samples = 0
            return
        snapshot = self.last_performance_snapshot
        high_cpu = max(5, self.settings.get_int("auto_cpu_high_percent"))
        high_memory = max(64, self.settings.get_int("auto_memory_high_mb"))
        warning_cpu = max(5, self.settings.get_int("auto_cpu_warning_percent"))
        if snapshot.average_cpu_percent >= warning_cpu:
            self._adaptive_fps_cap = min(self._adaptive_fps_cap or 20, 20)
        if (
            snapshot.average_cpu_percent >= high_cpu
            or snapshot.memory_mb >= high_memory
        ):
            self._auto_performance_samples += 1
        else:
            self._auto_performance_samples = max(0, self._auto_performance_samples - 1)
            return
        if self._auto_performance_samples < 3:
            return
        if self._auto_performance_applied:
            self._adaptive_fps_cap = 10
            self._check_power_policy()
            return
        self._auto_performance_applied = True
        self.settings.data.update(
            {
                "performance_profile": "economy",
                "fps": min(self.settings.get_int("fps"), 15),
                "low_power_mode": True,
                "optimize_videos": True,
            }
        )
        if self.settings.get_str("renderer") not in {"video", "image", "gif", "color"}:
            self.settings.data["effect_intensity"] = min(self.settings.get_int("effect_intensity"), 45)
        self.settings.save()
        self._adaptive_fps_cap = 10
        if self._start_native_compositor(pause_on_failure=False):
            self._report_status(
                "Assistente inteligente: consumo alto detectado. Perfil Leve e cache de video ativados."
            )
        else:
            self._report_status(
                "Assistente inteligente tentou reduzir o consumo, mas o compositor precisa ser reiniciado."
            )

    def _check_fullscreen_policy(self) -> None:
        if (
            self.last_backend != PresentationBackend.NATIVE_COMPOSITION
            or self._manually_paused
        ):
            return
        fullscreen = self.fullscreen_detector.has_foreground_fullscreen_app(
            self.native_compositor.process_ids | {os.getpid()}
        )
        if fullscreen:
            self._fullscreen_positive_samples += 1
            self._fullscreen_negative_samples = 0
        else:
            self._fullscreen_negative_samples += 1
            self._fullscreen_positive_samples = 0
        if fullscreen and not self._auto_paused and self._fullscreen_positive_samples >= 2:
            self.native_compositor.stop()
            self._native_paused = True
            self._auto_paused = True
            self._fullscreen_positive_samples = 0
            print("Movaura: compositor pausado por aplicativo em tela cheia.")
            self._update_tray_state()
            self._report_status("Animação pausada enquanto outro aplicativo ocupa a tela cheia.")
            return
        if (
            not fullscreen
            and self._auto_paused
            and not self._manually_paused
            and not self._session_paused
            and self._fullscreen_negative_samples >= 2
        ):
            if self._start_native_compositor():
                self._auto_paused = False
                self._fullscreen_negative_samples = 0
                print("Movaura: compositor retomado após sair da tela cheia.")
                self._update_tray_state()
                self._report_status("Animação retomada após sair da tela cheia.")

    def _update_tray_state(self) -> None:
        if self.tray:
            self.tray.update_state(self._native_paused)

    def _report_status(self, message: str) -> None:
        if self.status_callback:
            self.status_callback(message)

    def quit(self) -> None:
        self.stop()
        self.settings.save()
        self.app.quit()

    def _start_monitor(
        self,
        monitor: MonitorInfo,
        renderer_factory: RendererFactory,
        host_mode: HostMode,
    ) -> None:
        renderer = renderer_factory.create(self.settings)
        window = WallpaperWindow(renderer, f"Movaura Screen {monitor.index}")
        if host_mode in {
            HostMode.DESKTOP_CLICKTHROUGH,
            HostMode.DESKTOP_CLICKTHROUGH_TOP,
        }:
            window.enable_input_passthrough()
        window.setGeometry(monitor.x, monitor.y, monitor.width, monitor.height)
        window.show()
        self.app.processEvents()

        hwnd = int(window.winId())
        result = self.host.attach(
            hwnd,
            host_mode,
            monitor.x,
            monitor.y,
            monitor.width,
            monitor.height,
        )
        print(result.to_text())

        if not result.success and not result.should_keep_window:
            window.close()
            return

        window.start()
        self.windows.append(window)
