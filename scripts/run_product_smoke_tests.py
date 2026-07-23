from __future__ import annotations

import os
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QApplication

from core.monitor_manager import MonitorInfo
from core.media_analyzer import analyze_media
from core.native_compositor import NativeCompositorLaunchResult, NativeCompositorLauncher
from core.performance_monitor import PerformanceMonitor
from core.presentation_validator import PresentationValidator
from core.scene_package import ScenePackageManager
from core.scene_layers import normalize_layers, primary_effect
from core.scene_presets import ScenePresetManager
from core.benchmark import run_benchmark
from core.catalog import OnlineCatalog
from core.settings import MovauraSettings
from core.startup_manager import StartupManager
from core.update_checker import UpdateChecker, UpdateResult
from core.wallpaper_library import WallpaperLibrary
from ui.control_panel import ControlPanel
from ui.library_dialog import LibraryDialog
from ui.product_dialogs import SceneEditorDialog


class RecorderLauncher(NativeCompositorLauncher):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[dict] = []

    def launch_renderer(self, **kwargs) -> NativeCompositorLaunchResult:
        self.calls.append(kwargs)
        return NativeCompositorLaunchResult(True, "ok")

    def _stop_processes(self, processes) -> None:
        return None

    @staticmethod
    def _stop_orphaned_compositors() -> None:
        return None


def monitor(index: int, x: int, y: int, width: int, height: int) -> MonitorInfo:
    return MonitorInfo(index, f"DISPLAY{index}", QRect(x, y, width, height), 1.0, index == 0)


def test_resolution_matrix() -> None:
    cases = [
        [monitor(0, 0, 0, 1366, 768)],
        [monitor(0, 0, 0, 1920, 1080)],
        [monitor(0, 0, 0, 2560, 1440)],
        [monitor(0, 0, 0, 3840, 2160)],
        [monitor(0, 0, 0, 3440, 1440)],
        [monitor(0, 0, 0, 1920, 1080), monitor(1, -2560, 0, 2560, 1440)],
    ]
    for monitors in cases:
        launcher = RecorderLauncher()
        results = launcher.launch_monitors(monitors, "color", surface="desktop-live")
        assert all(result.success for result in results)
        geometry = launcher.calls[0]["geometry"]
        if len(monitors) == 1:
            assert geometry == (monitors[0].x, monitors[0].y, monitors[0].width, monitors[0].height)
        else:
            assert geometry == (-2560, 0, 4480, 1440)


def test_scene_package() -> None:
    with TemporaryDirectory() as temp:
        root = Path(temp)
        media = root / "background.webp"
        media.write_bytes(b"webp-placeholder")
        package = root / "scene.movaura"
        manager = ScenePackageManager(root / "imports")
        assert manager.export_scene(
            package,
            {
                "renderer": "audio",
                "media_path": str(media),
                "effect_intensity": 42,
                "effect_speed": 135,
            },
        ).success
        imported = manager.import_scene(package)
        assert imported.success, imported.message
        assert imported.settings and Path(str(imported.settings["media_path"])).is_file()
        assert imported.settings["effect_intensity"] == 42
        assert imported.settings["effect_speed"] == 135
        import zipfile
        with zipfile.ZipFile(package) as archive:
            assert any(name.startswith("thumbnail") for name in archive.namelist())


def test_validator() -> None:
    with TemporaryDirectory() as temp:
        media = Path(temp) / "background.webp"
        media.write_bytes(b"webp-placeholder")
        result = PresentationValidator().validate(
            {
                "experience_mode": "animated-desktop",
                "renderer": "parallax",
                "color": "#0078ff",
                "media_path": str(media),
                "fps": 30,
            }
        )
        assert result.success, result.message


def test_update_checker() -> None:
    with TemporaryDirectory() as temp:
        manifest = Path(temp) / "update.json"
        manifest.write_text(
            json.dumps(
                {
                    "version": "99.0.0",
                    "download_url": "https://example.com/Movaura-Setup.exe",
                    "sha256": "A" * 64,
                }
            ),
            encoding="utf-8",
        )
        result = UpdateChecker().check(manifest.as_uri())
        assert result.available, result.message
        manifest.write_text(
            json.dumps(
                {
                    "version": "99.0.0",
                    "download_url": "file:///unsafe-installer.exe",
                    "sha256": "not-a-real-hash".ljust(64, "0"),
                }
            ),
            encoding="utf-8",
        )
        result = UpdateChecker().check(manifest.as_uri())
        assert not result.available
        manifest.write_text(
            json.dumps(
                {
                    "version": "99.0.0",
                    "download_url": "http://example.com/Movaura-Setup.exe",
                    "sha256": "B" * 64,
                }
            ),
            encoding="utf-8",
        )
        result = UpdateChecker().check(manifest.as_uri())
        assert not result.available
        result = UpdateChecker().check("http://example.com/update.json")
        assert not result.available
        installer = Path(temp) / "Movaura-Setup.exe"
        installer.write_bytes(b"installer")
        digest = __import__("hashlib").sha256(installer.read_bytes()).hexdigest().upper()
        update = UpdateResult(True, "ok", "99.0.1", installer.as_uri(), digest)
        try:
            UpdateChecker().download(update)
        except ValueError as exc:
            assert "HTTPS" in str(exc)
        else:
            raise AssertionError("insecure update download should be blocked")


def test_startup_command() -> None:
    assert StartupManager().command


def test_library_recents() -> None:
    with TemporaryDirectory() as temp:
        library = WallpaperLibrary()
        library.metadata_path = Path(temp) / "library.json"
        library._metadata = {"favorites": [], "recent": [], "details": {}}
        item = library.items()[0]
        library.mark_recent(item)
        library.update_details(item, ["anime", " neon "], "Colecao teste")
        assert any(current.path == item.path and current.recent for current in library.items())
        current = next(current for current in library.items() if current.path == item.path)
        assert current.tags == ("anime", "neon")
        assert current.collection == "Colecao teste"
        assert current.resource_class in {"leve", "medio", "pesado"}


def test_media_analyzer() -> None:
    item = WallpaperLibrary().items()[0]
    analysis = analyze_media(item.path)
    assert analysis.kind in {"image", "gif", "video"}
    assert analysis.resource_class in {"leve", "medio", "pesado"}
    assert analysis.user_summary


def test_scene_layers_and_presets() -> None:
    with TemporaryDirectory() as temp:
        layers = normalize_layers([], "background.webp", "rain")
        layers.append({"name": "Vinheta", "kind": "effect", "effect": "vignette", "enabled": True})
        assert primary_effect(layers) == "vignette"
        manager = ScenePresetManager(Path(temp) / "presets.json")
        manager.save("Teste", {"scene_layers": layers})
        assert manager.load("Teste")
        assert manager.duplicate("Teste", "Copia")
        assert manager.delete("Copia")


def test_benchmark() -> None:
    result = run_benchmark(set(), duration_seconds=0)
    assert result.profile in {"economy", "adaptive", "quality"}


def test_catalog_source_resolution() -> None:
    with TemporaryDirectory() as temp:
        root = Path(temp)
        package_root = root / "package"
        catalog_dir = package_root / "data"
        video = package_root / "wallpapers" / "videos" / "clip.mp4"
        image = catalog_dir / "images" / "sample image.png"
        gif = catalog_dir / "gifs" / "loop.gif"
        video.parent.mkdir(parents=True)
        image.parent.mkdir(parents=True)
        gif.parent.mkdir(parents=True)
        video.write_bytes(b"fake-video")
        image.write_bytes(b"fake-image")
        gif.write_bytes(b"fake-gif")

        source = OnlineCatalog.resolve_source(
            "wallpapers/videos/clip.mp4",
            catalog_base=catalog_dir,
            package_root=package_root,
        )
        assert source.kind == "file"
        assert Path(source.value) == video.resolve(strict=False)

        source = OnlineCatalog.resolve_source(
            r"images\sample image.png",
            catalog_base=catalog_dir,
            package_root=package_root,
        )
        assert source.kind == "file"
        assert Path(source.value) == image.resolve(strict=False)

        manifest = catalog_dir / "catalog.json"
        manifest.write_text(
            json.dumps(
                {
                    "wallpapers": [
                        {"name": "Local Video", "kind": "video", "download_url": "wallpapers/videos/clip.mp4"},
                        {"name": "Local Image", "kind": "image", "download_url": "images/sample image.png"},
                        {"name": "Local Gif", "kind": "gif", "download_url": "gifs/loop.gif"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        items = OnlineCatalog().fetch(str(manifest))
        assert len(items) == 3
        assert all(item.catalog_base == catalog_dir for item in items)

        remote = OnlineCatalog.resolve_source("https://example.com/wallpaper.mp4")
        assert remote.kind == "url"
        try:
            OnlineCatalog.resolve_source("wallpapers/videos/missing.mp4", catalog_dir, package_root)
        except FileNotFoundError as exc:
            assert "Arquivo do catalogo nao encontrado" in str(exc)
            assert "unknown url type" not in str(exc)
        else:
            raise AssertionError("missing relative catalog item should fail clearly")

        try:
            OnlineCatalog.resolve_source("../outside.mp4", catalog_dir, package_root)
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("path traversal must not resolve outside catalog/package roots")


def test_local_catalog() -> None:
    items = OnlineCatalog().fetch("")
    assert items
    downloaded = OnlineCatalog().download(items[0])
    assert downloaded.is_file()
    assert WallpaperLibrary.kind_for_path(downloaded) == "image"


def test_performance_snapshot() -> None:
    snapshot = PerformanceMonitor().sample(set())
    assert snapshot.average_cpu_percent == 0.0
    assert "média" in snapshot.to_text()


def test_panel() -> None:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory() as temp:
        settings = MovauraSettings.load(Path(temp) / "settings.json")
        panel = ControlPanel(app, settings)
        library = LibraryDialog(WallpaperLibrary())
        editor = SceneEditorDialog(settings)
        assert panel.quick_screen_combo.count() >= 1
        assert panel.quick_stop_preview_button.isEnabled()
        assert panel.quick_optimize_button.isEnabled()
        assert panel.quick_catalog_button.isEnabled()
        assert panel.auto_performance_checkbox.isChecked()
        assert panel.auto_cpu_spin.value() >= 5
        assert panel.auto_memory_spin.value() >= 64
        assert panel.performance_combo.count() == 3
        assert library.filter_combo.count() == 11
        assert library.sort_combo.count() == 3
        assert editor.effect.count() == 9
        assert editor.layer_list.count() >= 2
        assert editor.intensity.value() == settings.get_int("effect_intensity")
        assert editor.speed.value() == settings.get_int("effect_speed")
        library.close()
        editor.close()
        panel.close()


def main() -> None:
    WallpaperLibrary().stats()
    test_resolution_matrix()
    test_scene_package()
    test_validator()
    test_update_checker()
    test_startup_command()
    test_library_recents()
    test_media_analyzer()
    test_performance_snapshot()
    test_scene_layers_and_presets()
    test_benchmark()
    test_catalog_source_resolution()
    test_local_catalog()
    test_panel()
    print("product_smoke_tests=ok")


if __name__ == "__main__":
    main()
