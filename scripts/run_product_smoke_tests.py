from __future__ import annotations

import os
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QRect, QUrl
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

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
from core.thumbnail_cache import ThumbnailCache
from ui.control_panel import ControlPanel
from ui.library_dialog import LibraryDialog
from ui.pages.explore_page import ExplorePage
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
        malicious = root / "malicious.movaura"
        with zipfile.ZipFile(malicious, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("scene.json", "{}")
            archive.writestr("../escape.txt", "bad")
        assert not manager.import_scene(malicious).success
        script_package = root / "script.movaura"
        with zipfile.ZipFile(script_package, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "scene.json",
                json.dumps({"format": "movaura-scene", "version": 1, "settings": {}}),
            )
            archive.writestr("media/run.ps1", "bad")
        assert not manager.import_scene(script_package).success


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
        root = Path(temp)
        library = WallpaperLibrary()
        library.included_root = root / "included"
        library.personal_root = root / "personal"
        library.personal_root.mkdir(parents=True, exist_ok=True)
        library.metadata_path = root / "library.json"
        library._metadata = {"favorites": [], "recent": [], "details": {}}
        source = root / "smoke-wallpaper.png"
        source.write_bytes(b"png-placeholder")
        imported = library.import_files([source])
        assert imported
        item = imported[0]
        duplicate = library.import_files([source])
        assert duplicate and duplicate[0].path == item.path
        assert len(library.items()) == 1
        library.mark_recent(item)
        library.update_details(item, ["anime", " neon "], "Colecao teste")
        assert any(current.path == item.path and current.recent for current in library.items())
        current = next(current for current in library.items() if current.path == item.path)
        assert current.tags == ("anime", "neon")
        assert current.collection == "Colecao teste"
        assert current.category == "Anime"
        assert current.resource_class in {"leve", "medio", "pesado"}
        renamed = library.rename_personal(current, "Novo Nome Seguro")
        assert renamed
        assert renamed.path.name == "Novo Nome Seguro.png"
        assert not current.path.exists()
        library.update_ui_state(search="anime", filter="Anime", sort="Favoritos primeiro")
        assert library.ui_state()["filter"] == "Anime"


def test_media_analyzer() -> None:
    with TemporaryDirectory() as temp:
        media = Path(temp) / "smoke-wallpaper.png"
        media.write_bytes(b"png-placeholder")
        analysis = analyze_media(media)
        assert analysis.kind == "image"
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


def test_explore_external_urls() -> None:
    url = ExplorePage.build_external_url("Pexels", "cyberpunk city")
    assert url == "https://www.pexels.com/search/cyberpunk+city/"
    assert ExplorePage.is_allowed_external_url(url)
    assert ExplorePage.is_allowed_external_url("https://pixabay.com/images/search/anime+wallpaper/")
    assert ExplorePage.is_allowed_external_url("https://unsplash.com/s/photos/space+station")
    assert ExplorePage.is_allowed_external_url("https://wallhaven.cc/search?q=sci-fi")
    assert not ExplorePage.is_allowed_external_url("http://www.pexels.com/search/cyberpunk/")
    assert not ExplorePage.is_allowed_external_url("https://evil.example/search?q=cyberpunk")
    special = ExplorePage.build_external_url("Wallhaven", "ação & espaço")
    assert "a%C3%A7%C3%A3o+%26+espa%C3%A7o" in special


def test_explore_page_without_api_key() -> None:
    with TemporaryDirectory() as temp:
        settings = MovauraSettings.load(Path(temp) / "settings.json")
        settings.data["pexels_api_key"] = "legacy-secret"
        app = QApplication.instance() or QApplication([])
        library = WallpaperLibrary()
        page = ExplorePage(settings, library)
        assert "pexels_api_key" not in settings.data
        assert "API" not in page.status_label.text()
        assert page.import_button.isEnabled()
        assert not page.apply_button.isEnabled()
        page.close()


def test_explore_local_import_flow() -> None:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory() as temp:
        root = Path(temp)
        settings = MovauraSettings.load(root / "settings.json")
        library = WallpaperLibrary()
        library.included_root = root / "included"
        library.personal_root = root / "personal"
        library.personal_root.mkdir(parents=True, exist_ok=True)
        library.metadata_path = root / "library.json"
        library._metadata = {"favorites": [], "recent": [], "details": {}}
        page = ExplorePage(settings, library)

        assert page.import_paths([]) == []
        assert "cancelada" in page.status_label.text().lower()

        invalid = root / "invalid.txt"
        invalid.write_text("not a wallpaper", encoding="utf-8")
        assert page.import_paths([invalid]) == []
        assert "compativel" in page.status_label.text().lower()

        source = root / "wallpaper.png"
        image = QImage(64, 36, QImage.Format.Format_RGB32)
        image.fill(0x0078FF)
        assert image.save(str(source))

        imported = page.import_paths([source])
        assert len(imported) == 1
        assert page.last_imported is imported[0]
        assert page.apply_button.isEnabled()
        assert page.favorite_button.isEnabled()
        assert source.is_file()
        assert imported[0].path.is_file()
        assert imported[0].path.is_relative_to(library.personal_root)

        page._favorite_imported()
        assert any(item.favorite for item in library.items())

        duplicated = page.import_paths([source])
        assert duplicated
        assert len(library.items()) == 1
        assert "ignorado" in page.status_label.text().lower()
        page.close()


class FakeMimeData:
    def __init__(self, urls: list[QUrl]) -> None:
        self._urls = urls

    def hasUrls(self) -> bool:
        return bool(self._urls)

    def urls(self) -> list[QUrl]:
        return self._urls


class FakeDropEvent:
    def __init__(self, urls: list[QUrl]) -> None:
        self._mime = FakeMimeData(urls)

    def mimeData(self) -> FakeMimeData:
        return self._mime


def test_library_dialog_filters_drag_and_cache() -> None:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory() as temp:
        root = Path(temp)
        image = QImage(80, 45, QImage.Format.Format_RGB32)
        image.fill(0x00AA88)
        anime = root / "anime-neon.png"
        invalid = root / "notes.txt"
        assert image.save(str(anime))
        invalid.write_text("ignore", encoding="utf-8")

        library = WallpaperLibrary()
        library.included_root = root / "included"
        library.personal_root = root / "personal"
        library.personal_root.mkdir(parents=True, exist_ok=True)
        library.metadata_path = root / "library.json"
        library._metadata = {"favorites": [], "recent": [], "details": {}, "ui": {}}
        dialog = LibraryDialog(library)

        imported = dialog.import_paths([anime, invalid])
        assert len(imported) == 1
        dialog.search_edit.setText("anime")
        dialog.filter_combo.setCurrentText("Anime")
        dialog.sort_combo.setCurrentText("Favoritos primeiro")
        dialog.refresh()
        assert dialog.list_widget.count() == 1
        assert library.ui_state()["search"] == "anime"
        assert library.ui_state()["filter"] == "Anime"
        assert library.ui_state()["sort"] == "Favoritos primeiro"

        supported = dialog._supported_drop_paths(
            FakeDropEvent(
                [
                    QUrl.fromLocalFile(str(anime)),
                    QUrl.fromLocalFile(str(invalid)),
                    QUrl("https://example.com/wallpaper.png"),
                ]
            )
        )
        assert supported == [anime]
        cache = ThumbnailCache(dialog)
        assert cache.cached_path(imported[0].path) == cache.cached_path(imported[0].path)
        dialog.close()


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
        tab_names = [panel.tabs.tabText(index) for index in range(panel.tabs.count())]
        assert "Explorar" in tab_names
        assert "Gerar com IA" in tab_names
        assert panel.explore_page.import_button.isEnabled()
        assert not hasattr(panel.ai_generation_page, "prompt_edit")
        assert not hasattr(panel.ai_generation_page, "generate_button")
        assert panel.ai_generation_page.shutdown()
        assert panel.quick_screen_combo.count() >= 1
        assert panel.quick_stop_preview_button.isEnabled()
        assert panel.quick_optimize_button.isEnabled()
        assert panel.quick_catalog_button.isEnabled()
        assert panel.auto_performance_checkbox.isChecked()
        assert panel.auto_cpu_spin.value() >= 5
        assert panel.auto_memory_spin.value() >= 64
        assert panel.performance_combo.count() == 3
        assert library.filter_combo.count() == 16
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
    test_explore_external_urls()
    test_explore_page_without_api_key()
    test_explore_local_import_flow()
    test_library_dialog_filters_drag_and_cache()
    test_panel()
    print("product_smoke_tests=ok")


if __name__ == "__main__":
    main()
