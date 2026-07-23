from __future__ import annotations

import ctypes
import subprocess
import time
from threading import Lock, Thread
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.monitor_manager import MonitorInfo
from core.runtime_paths import resource_root


@dataclass(frozen=True)
class NativeCompositorLaunchResult:
    success: bool
    message: str
    path: Path | None = None


class NativeCompositorLauncher:
    def __init__(self, executable: Path | None = None) -> None:
        self.executable = executable or self.default_executable()
        self.processes: dict[str, subprocess.Popen[Any]] = {}
        self._generation = 0
        self._process_lock = Lock()

    @staticmethod
    def default_executable() -> Path:
        root = resource_root()
        candidates = [
            root
            / "native_compositor_app"
            / "bin"
            / "movaura_native_compositor.exe",
            root
            / "native_compositor_app"
            / "build-movaura-nmake"
            / "bin"
            / "movaura_native_compositor.exe",
            root
            / "native_compositor_app"
            / "build-nmake"
            / "bin"
            / "movaura_native_compositor.exe",
            root
            / "native_compositor_app"
            / "build"
            / "bin"
            / "Release"
            / "movaura_native_compositor.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def launch_preview(
        self,
        color: str = "#0078ff",
        fps: int = 30,
        scene: str = "pulse",
        media_path: str = "",
        replace_existing: bool = False,
        instance_key: str = "preview",
        geometry: tuple[int, int, int, int] | None = None,
        repeat_regions: list[tuple[int, int, int, int]] | None = None,
        fullscreen: bool = False,
        desktop_experimental: bool = False,
        desktop_live: bool = False,
        effect_intensity: int = 70,
        effect_speed: int = 100,
        video_max_size: tuple[int, int] | None = None,
        prefer_low_cpu: bool = False,
    ) -> NativeCompositorLaunchResult:
        if not self.executable.exists():
            return NativeCompositorLaunchResult(
                False,
                f"executável do compositor nativo não encontrado: {self.executable}",
                self.executable,
            )

        try:
            arguments = [
                str(self.executable),
                "--color",
                color,
                "--fps",
                str(max(1, min(fps, 60))),
                "--scene",
                scene,
                "--instance-key",
                instance_key,
                "--effect-intensity",
                str(max(0, min(effect_intensity, 100))),
                "--effect-speed",
                str(max(10, min(effect_speed, 200))),
            ]
            if media_path:
                arguments.extend(["--file", media_path])
            if prefer_low_cpu:
                arguments.append("--prefer-low-cpu")
            if video_max_size:
                max_width, max_height = video_max_size
                arguments.extend(
                    [
                        "--video-max-width",
                        str(max(320, min(int(max_width), 1920))),
                        "--video-max-height",
                        str(max(240, min(int(max_height), 1080))),
                    ]
                )
            if replace_existing:
                arguments.append("--replace-existing")
            if fullscreen:
                arguments.append("--fullscreen")
            if desktop_experimental:
                arguments.append("--desktop-experimental")
            if desktop_live:
                arguments.append("--desktop-live")
            if geometry:
                x, y, width, height = geometry
                width = max(1, int(width))
                height = max(1, int(height))
                arguments.extend(
                    [
                        "--x",
                        str(x),
                        "--y",
                        str(y),
                        "--width",
                        str(width),
                        "--height",
                        str(height),
                    ]
                )
            for x, y, width, height in repeat_regions or []:
                arguments.extend(
                    [
                        "--repeat-monitor",
                        f"{x},{y},{width},{height}",
                    ]
                )
            process = subprocess.Popen(arguments)
            self.processes[instance_key] = process
        except OSError as exc:
            return NativeCompositorLaunchResult(
                False,
                f"falha ao iniciar compositor nativo: {exc}",
                self.executable,
            )

        time.sleep(0.35 if desktop_live else 0.15)
        return_code = process.poll()
        if return_code is not None:
            self.processes.pop(instance_key, None)
            return NativeCompositorLaunchResult(
                False,
                f"compositor nativo encerrou ao iniciar (código {return_code})",
                self.executable,
            )

        if desktop_live:
            message = "compositor nativo iniciado na área de trabalho"
        elif desktop_experimental:
            message = "compositor nativo iniciado na pilha experimental do Progman"
        elif fullscreen:
            message = "compositor nativo iniciado em janela de teste em tela cheia"
        else:
            message = "pré-visualização do compositor nativo iniciada em janela segura"
        return NativeCompositorLaunchResult(True, message, self.executable)

    def launch_renderer(
        self,
        renderer: str,
        color: str = "#0078ff",
        fps: int = 30,
        media_path: str = "",
        instance_key: str = "engine",
        geometry: tuple[int, int, int, int] | None = None,
        repeat_regions: list[tuple[int, int, int, int]] | None = None,
        stop_existing: bool = True,
        fullscreen: bool = False,
        desktop_experimental: bool = False,
        desktop_live: bool = False,
        effect_intensity: int = 70,
        effect_speed: int = 100,
    ) -> NativeCompositorLaunchResult:
        scene = self.scene_for_renderer(renderer, media_path)
        if scene in {"image", "gif", "video"}:
            if not media_path:
                return NativeCompositorLaunchResult(
                    False,
                    f"a cena nativa {scene} exige um arquivo de mídia",
                    self.executable,
                )
            if not Path(media_path).expanduser().exists():
                return NativeCompositorLaunchResult(
                    False,
                    f"arquivo de mídia não encontrado: {media_path}",
                    self.executable,
                )
        if scene in {"audio", "parallax", "particles", "rain", "fog", "glow", "vignette"} and media_path:
            if not Path(media_path).expanduser().exists():
                return NativeCompositorLaunchResult(
                    False,
                    f"arquivo usado como fundo não encontrado: {media_path}",
                    self.executable,
                )

        video_max_size = self._video_decode_limit(
            scene=scene,
            fps=fps,
            geometry=geometry,
            repeat_regions=repeat_regions,
        )
        prefer_low_cpu = scene == "video" and (fps <= 20 or bool(repeat_regions))

        if stop_existing:
            self.stop()
        return self.launch_preview(
            color=color,
            fps=fps,
            scene=scene,
            media_path=media_path,
            replace_existing=True,
            instance_key=instance_key,
            geometry=geometry,
            repeat_regions=repeat_regions,
            fullscreen=fullscreen,
            desktop_experimental=desktop_experimental,
            desktop_live=desktop_live,
            effect_intensity=effect_intensity,
            effect_speed=effect_speed,
            video_max_size=video_max_size,
            prefer_low_cpu=prefer_low_cpu,
        )

    def stop(self) -> None:
        with self._process_lock:
            processes = self.processes
            self.processes = {}
        self._stop_processes(processes)

    def _stop_processes(self, processes: dict[str, subprocess.Popen[Any]]) -> None:
        for process in processes.values():
            if process.poll() is not None:
                continue
            try:
                self._request_close(process.pid)
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    process.terminate()
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    try:
                        process.kill()
                        process.wait(timeout=1)
                    except OSError:
                        pass
                except OSError:
                    pass
            except OSError:
                pass

    @staticmethod
    def _stop_orphaned_compositors() -> None:
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            subprocess.run(
                ["taskkill", "/f", "/im", "movaura_native_compositor.exe"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
        except OSError:
            pass

    @staticmethod
    def _has_visible_window(pid: int) -> bool:
        user32 = ctypes.windll.user32
        found = ctypes.c_bool(False)
        callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        @callback_type
        def visit(hwnd, _lparam):
            window_pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
            if window_pid.value == pid and user32.IsWindowVisible(hwnd):
                found.value = True
                return False
            return True

        @callback_type
        def visit_top_level(hwnd, _lparam):
            if not visit(hwnd, 0):
                return False
            user32.EnumChildWindows(hwnd, visit, 0)
            return not found.value

        user32.EnumWindows(visit_top_level, 0)
        return found.value

    def _wait_until_visible(
        self,
        processes: dict[str, subprocess.Popen[Any]],
        timeout_seconds: float = 2.5,
    ) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if all(
                process.poll() is None and self._has_visible_window(process.pid)
                for process in processes.values()
            ):
                return True
            time.sleep(0.04)
        return False

    @staticmethod
    def _request_close(pid: int) -> None:
        user32 = ctypes.windll.user32
        callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        @callback_type
        def close_matching(hwnd, _lparam):
            window_pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
            if window_pid.value == pid:
                user32.PostMessageW(hwnd, 0x0010, 0, 0)
            return True

        @callback_type
        def visit_top_level(hwnd, _lparam):
            close_matching(hwnd, 0)
            user32.EnumChildWindows(hwnd, close_matching, 0)
            return True

        user32.EnumWindows(visit_top_level, 0)

    @property
    def is_running(self) -> bool:
        return any(process.poll() is None for process in self.processes.values())

    @property
    def running_count(self) -> int:
        return sum(process.poll() is None for process in self.processes.values())

    @property
    def expected_count(self) -> int:
        return len(self.processes)

    @property
    def process_ids(self) -> set[int]:
        return {
            process.pid
            for process in self.processes.values()
            if process.poll() is None
        }

    def launch_monitors(
        self,
        monitors: list[MonitorInfo],
        renderer: str,
        color: str = "#0078ff",
        fps: int = 30,
        media_path: str = "",
        surface: str = "preview",
        multi_monitor_mode: str = "repeat",
        assignments: dict[str, dict[str, str]] | None = None,
        effect_intensity: int = 70,
        effect_speed: int = 100,
    ) -> list[NativeCompositorLaunchResult]:
        with self._process_lock:
            previous_processes = self.processes
            self.processes = {}
            self._generation += 1
        if not previous_processes:
            self._stop_orphaned_compositors()
        results = []
        configured_assignments = assignments or {}
        if surface == "desktop-live" and configured_assignments:
            results.extend(
                self._launch_assigned_monitor_surfaces(
                    monitors=monitors,
                    assignments=configured_assignments,
                    fallback_renderer=renderer,
                    fallback_color=color,
                    fallback_fps=fps,
                    fallback_media_path=media_path,
                    fallback_effect_intensity=effect_intensity,
                    fallback_effect_speed=effect_speed,
                )
            )
        elif surface == "desktop-live" and len(monitors) > 1:
            left = min(monitor.x for monitor in monitors)
            top = min(monitor.y for monitor in monitors)
            right = max(monitor.x + monitor.width for monitor in monitors)
            bottom = max(monitor.y + monitor.height for monitor in monitors)
            repeat_regions = None
            instance_key = f"desktop-span-g{self._generation}"
            if multi_monitor_mode != "span":
                instance_key = f"desktop-repeat-g{self._generation}"
                repeat_regions = [
                    (
                        monitor.x - left,
                        monitor.y - top,
                        monitor.width,
                        monitor.height,
                    )
                    for monitor in monitors
                ]
            results.append(
                self.launch_renderer(
                    renderer=renderer,
                    color=color,
                    fps=fps,
                    media_path=media_path,
                    instance_key=instance_key,
                    geometry=(left, top, right - left, bottom - top),
                    repeat_regions=repeat_regions,
                    stop_existing=False,
                    desktop_live=True,
                    effect_intensity=effect_intensity,
                    effect_speed=effect_speed,
                )
            )
        else:
            results.extend(
                self._launch_monitor_surfaces(
                    monitors=monitors,
                    renderer=renderer,
                    color=color,
                    fps=fps,
                    media_path=media_path,
                    surface=surface,
                    effect_intensity=effect_intensity,
                    effect_speed=effect_speed,
                )
            )
        success = bool(results) and all(result.success for result in results)
        current_processes = self.processes
        if previous_processes and success:
            Thread(
                target=self._retire_previous_when_ready,
                args=(current_processes, previous_processes),
                daemon=True,
            ).start()
        elif previous_processes:
            self._stop_processes(current_processes)
            with self._process_lock:
                if self.processes is current_processes:
                    self.processes = previous_processes
        elif not success:
            self._stop_processes(current_processes)
            with self._process_lock:
                if self.processes is current_processes:
                    self.processes = {}
        return results

    def _launch_assigned_monitor_surfaces(
        self,
        monitors: list[MonitorInfo],
        assignments: dict[str, dict[str, str]],
        fallback_renderer: str,
        fallback_color: str,
        fallback_fps: int,
        fallback_media_path: str,
        fallback_effect_intensity: int,
        fallback_effect_speed: int,
    ) -> list[NativeCompositorLaunchResult]:
        results = []
        for monitor in monitors:
            assignment = assignments.get(str(monitor.index), {})
            results.append(
                self.launch_renderer(
                    renderer=str(assignment.get("renderer", fallback_renderer)),
                    color=str(assignment.get("color", fallback_color)),
                    fps=int(assignment.get("fps", fallback_fps)),
                    media_path=str(assignment.get("media_path", fallback_media_path)),
                    instance_key=f"assigned-monitor-{monitor.index}-g{self._generation}",
                    geometry=(monitor.x, monitor.y, monitor.width, monitor.height),
                    stop_existing=False,
                    desktop_live=True,
                    effect_intensity=int(assignment.get("effect_intensity", fallback_effect_intensity)),
                    effect_speed=int(assignment.get("effect_speed", fallback_effect_speed)),
                )
            )
        return results

    def _launch_monitor_surfaces(
        self,
        monitors: list[MonitorInfo],
        renderer: str,
        color: str,
        fps: int,
        media_path: str,
        surface: str,
        effect_intensity: int,
        effect_speed: int,
    ) -> list[NativeCompositorLaunchResult]:
        results = []
        for monitor in monitors:
            fullscreen = surface == "fullscreen"
            desktop_experimental = surface == "desktop-experimental"
            desktop_live = surface == "desktop-live"
            if fullscreen or desktop_experimental or desktop_live:
                geometry = (monitor.x, monitor.y, monitor.width, monitor.height)
            else:
                width = min(960, max(320, monitor.width - 80))
                height = min(540, max(240, monitor.height - 80))
                geometry = (
                    monitor.x + max(20, (monitor.width - width) // 2),
                    monitor.y + max(20, (monitor.height - height) // 2),
                    width,
                    height,
                )
            results.append(
                self.launch_renderer(
                    renderer=renderer,
                    color=color,
                    fps=fps,
                    media_path=media_path,
                    instance_key=f"monitor-{monitor.index}-g{self._generation}",
                    geometry=geometry,
                    stop_existing=False,
                    fullscreen=fullscreen,
                    desktop_experimental=desktop_experimental,
                    desktop_live=desktop_live,
                    effect_intensity=effect_intensity,
                    effect_speed=effect_speed,
                )
            )
        return results

    def _retire_previous_when_ready(
        self,
        current_processes: dict[str, subprocess.Popen[Any]],
        previous_processes: dict[str, subprocess.Popen[Any]],
    ) -> None:
        if self._wait_until_visible(current_processes):
            self._stop_processes(previous_processes)
            return
        self._stop_processes(current_processes)
        with self._process_lock:
            if self.processes is current_processes:
                self.processes = previous_processes

    @staticmethod
    def scene_for_renderer(renderer: str, media_path: str = "") -> str:
        if renderer == "video":
            return "video"
        if renderer == "gif":
            return "gif"
        if renderer == "color":
            return "solid"
        if renderer == "audio":
            return "audio"
        if renderer == "parallax":
            return "parallax"
        if renderer in {"particles", "rain", "fog", "glow", "vignette"}:
            return renderer
        if renderer == "image":
            return "image"
        suffix = Path(media_path).suffix.lower() if media_path else ""
        if suffix in {".png", ".jpg", ".jpeg", ".bmp"}:
            return "image"
        return "pulse"

    @staticmethod
    def _video_decode_limit(
        scene: str,
        fps: int,
        geometry: tuple[int, int, int, int] | None,
        repeat_regions: list[tuple[int, int, int, int]] | None,
    ) -> tuple[int, int] | None:
        if scene != "video":
            return None
        if fps <= 15:
            return (1280, 720)
        if fps <= 30:
            return (1440, 810) if repeat_regions else (1600, 900)
        if geometry:
            _, _, width, height = geometry
            if width <= 1600 and height <= 900:
                return (1600, 900)
        return (1920, 1080)
