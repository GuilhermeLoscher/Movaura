"""Movaura desktop engine. Desenvolvido por Guilherme Loscher (GL)."""

import argparse
import signal
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.app_logging import configure_logging
from core.desktop_host import HostMode
from core.engine import MovauraEngine
from core.explorer_repair import ExplorerHostRepair
from core.license_manager import LicenseManager
from core.native_host import NativeHost
from core.self_test import run_self_test
from core.native_compositor import NativeCompositorLauncher
from core.presentation_validator import PresentationValidator
from core.settings import MovauraSettings
from core.screensaver import ScreensaverSession
from core.single_instance import SingleInstanceGuard
from core.runtime_paths import app_icon_path
from core.startup_manager import StartupManager
from core.system_wallpaper import SystemWallpaperBackend
from core.version import APP_VERSION
from ui.activation_dialog import ActivationDialog
from ui.control_panel import ControlPanel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"Movaura {APP_VERSION}")
    parser.add_argument("--mode", choices=[mode.value for mode in HostMode], help="Modo de hospedagem no desktop.")
    parser.add_argument(
        "--renderer",
        help="Renderizador inicial: color, image, video, gif, opengl ou id de plugin.",
    )
    parser.add_argument("--file", help="Arquivo de mÃ­dia para imagem, vÃ­deo ou GIF.")
    parser.add_argument("--color", help="Cor hexadecimal para renderizadores compatÃ­veis.")
    parser.add_argument("--fps", type=int, help="FPS desejado para renderizadores animados.")
    parser.add_argument("--screen", type=int, help="Iniciar somente no Ã­ndice de monitor informado.")
    parser.add_argument(
        "--native-surface",
        choices=["preview", "fullscreen", "desktop-experimental", "desktop-live"],
        help="Tipo de superfÃ­cie do compositor nativo.",
    )
    parser.add_argument("--diagnose", action="store_true", help="Exibir diagnÃ³stico do Explorer.")
    parser.add_argument(
        "--repair-explorer-host",
        action="store_true",
        help="Reiniciar o Explorer e consultar WorkerW/Progman novamente.",
    )
    parser.add_argument(
        "--reset-experimental-host",
        action="store_true",
        help="Ocultar WorkerW do Explorer alterados durante testes experimentais.",
    )
    parser.add_argument(
        "--native-diagnose",
        action="store_true",
        help="Executar diagnÃ³stico da DLL native_host e sair.",
    )
    parser.add_argument(
        "--restore-system-wallpaper",
        action="store_true",
        help="Restaurar o wallpaper salvo antes do fallback estÃ¡tico seguro.",
    )
    parser.add_argument(
        "--native-composition-preview",
        action="store_true",
        help="Abrir uma prÃ©-visualizaÃ§Ã£o segura com DirectComposition e sair.",
    )
    parser.add_argument(
        "--native-scene",
        choices=["pulse", "solid", "image", "gif", "video"],
        default="pulse",
        help="Cena da prÃ©-visualizaÃ§Ã£o do compositor nativo.",
    )
    parser.add_argument(
        "--control-panel",
        action="store_true",
        help="Abrir o painel grÃ¡fico do Movaura.",
    )
    parser.add_argument(
        "--run-wallpaper",
        action="store_true",
        help="Iniciar o wallpaper salvo sem abrir o painel. Uso tecnico/manual.",
    )
    parser.add_argument(
        "--startup",
        action="store_true",
        help="Aplicar silenciosamente o wallpaper salvo e sair.",
    )
    parser.add_argument(
        "--enable-startup",
        action="store_true",
        help="Ativar a inicializacao automatica do Movaura e sair.",
    )
    parser.add_argument(
        "--disable-startup",
        action="store_true",
        help="Remover a inicializacao automatica do Movaura e sair.",
    )
    parser.add_argument("--no-tray", action="store_true", help="Desativar o Ã­cone da bandeja.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Executar autoteste de distribuiÃ§Ã£o e sair.",
    )
    parser.add_argument("--screensaver", action="store_true", help="Executar como protetor de tela.")
    return parser.parse_args()


def should_open_control_panel(args: argparse.Namespace) -> bool:
    if args.control_panel:
        return True
    presentation_args = (
        args.run_wallpaper,
        args.diagnose,
        args.mode,
        args.renderer,
        args.file,
        args.color,
        args.fps,
        args.screen is not None,
        args.native_surface,
        args.repair_explorer_host,
        args.reset_experimental_host,
    )
    return not any(bool(value) for value in presentation_args)


def apply_cli_overrides(settings: MovauraSettings, args: argparse.Namespace) -> None:
    if args.mode:
        settings.data["host_mode"] = args.mode
    if args.renderer:
        settings.data["renderer"] = args.renderer
    if args.file:
        settings.data["media_path"] = str(Path(args.file).expanduser())
    if args.color:
        settings.data["color"] = args.color
    if args.fps:
        settings.data["fps"] = max(1, min(args.fps, 60))
    if args.screen is not None:
        settings.data["screen"] = args.screen
    if args.native_surface:
        settings.data["native_surface"] = args.native_surface
    if args.mode == "system-wallpaper":
        settings.data["experience_mode"] = "desktop-static"
    elif args.mode == "native-composition":
        if args.native_surface == "fullscreen":
            settings.data["experience_mode"] = "fullscreen-test"
        elif args.native_surface == "desktop-live":
            settings.data["experience_mode"] = "animated-desktop"
        else:
            settings.data["experience_mode"] = "animated-preview"
    if args.no_tray:
        settings.data["tray_enabled"] = False


def main() -> int:
    configure_logging()
    raw_arguments = [argument.lower() for argument in sys.argv[1:]]
    if any(argument.startswith("/p") for argument in raw_arguments):
        return 0
    if any(argument.startswith("/c") for argument in raw_arguments):
        sys.argv = [sys.argv[0], "--control-panel"]
    elif any(argument.lower() in {"/s", "-s"} for argument in raw_arguments):
        sys.argv = [sys.argv[0], "--screensaver"]
    args = parse_args()

    if args.enable_startup:
        result = StartupManager().set_enabled(True)
        print(f"Movaura startup enable: success={result.success} reason={result.message}")
        return 0 if result.success else 2
    if args.disable_startup:
        result = StartupManager().set_enabled(False)
        print(f"Movaura startup disable: success={result.success} reason={result.message}")
        return 0
    if args.native_diagnose:
        print(NativeHost().probe_text())
        return 0
    if args.self_test:
        result = run_self_test()
        print(result.to_text())
        return 0 if result.success else 3
    if args.restore_system_wallpaper:
        result = SystemWallpaperBackend().restore()
        print(f"Movaura system wallpaper restore: success={result.success} reason={result.message}")
        if result.path:
            print(f"  path: {result.path}")
        return 0
    if args.native_composition_preview:
        result = NativeCompositorLauncher().launch_preview(
            color=args.color or "#0078ff",
            fps=args.fps or 30,
            scene=args.native_scene,
            media_path=str(Path(args.file).expanduser()) if args.file else "",
        )
        print(f"Movaura native compositor preview: success={result.success} reason={result.message}")
        if result.path:
            print(f"  path: {result.path}")
        return 0
    if args.screensaver:
        app = QApplication(sys.argv)
        settings = MovauraSettings.load_default()
        session = ScreensaverSession(app, settings)
        if not session.start():
            return 2
        return app.exec()

    instance_guard = SingleInstanceGuard()
    if instance_guard.already_running:
        print("Movaura jÃ¡ estÃ¡ em execuÃ§Ã£o. Use o Ã­cone da bandeja para abrir o painel.")
        return 0

    app = QApplication(sys.argv)
    app.setApplicationName("Movaura")
    app.setOrganizationName("Guilherme Loscher")
    app.setApplicationVersion(APP_VERSION)
    app.setWindowIcon(QIcon(str(app_icon_path())))
    app.setQuitOnLastWindowClosed(False)
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    signal_timer = QTimer()
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start(250)

    settings = MovauraSettings.load_default()
    apply_cli_overrides(settings, args)
    settings.save()

    license_manager = LicenseManager(settings)
    license_status = license_manager.status()
    if license_status.required and not license_status.active:
        if args.startup:
            print(f"Movaura Beta nao ativado: {license_status.message}")
            return 2
        activation_dialog = ActivationDialog(license_manager)
        if activation_dialog.exec() != ActivationDialog.DialogCode.Accepted:
            return 2

    if args.startup:
        if (
            settings.get_str("experience_mode") == "desktop-static"
            and settings.get_str("renderer") in {"color", "image"}
        ):
            result = SystemWallpaperBackend().apply(
                settings.get_str("renderer"),
                settings.get_str("color"),
                settings.get_str("media_path"),
                settings.get_str("wallpaper_position"),
            )
            print(f"Movaura startup wallpaper: success={result.success} reason={result.message}")
            return 0
        validation = PresentationValidator().validate(settings.data)
        if not validation.success:
            print(f"Movaura startup: configuraÃ§Ã£o invÃ¡lida: {validation.message}")
            return 2
        engine = MovauraEngine(app, settings, diagnose=False, quit_when_no_windows=False)
        engine.start()
        return app.exec()

    if should_open_control_panel(args):
        panel = ControlPanel(app, settings)
        panel.show()
        return app.exec()

    diagnose_engine = args.diagnose
    if args.reset_experimental_host:
        report = ExplorerHostRepair().hide_forced_workerws()
        print(report.to_text())
        return 0

    if args.repair_explorer_host:
        report = ExplorerHostRepair().restart_explorer_and_probe()
        print(report.to_text())
        diagnose_engine = False

    if settings.get_str("host_mode") in {"native-composition", "system-wallpaper"}:
        validation = PresentationValidator().validate(settings.data)
        if not validation.success:
            print(f"Movaura: configuraÃ§Ã£o invÃ¡lida: {validation.message}")
            return 2

    engine = MovauraEngine(app, settings, diagnose=diagnose_engine)
    engine.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())



