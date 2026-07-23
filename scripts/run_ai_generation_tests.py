from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from threading import Event

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication

from core.ai_generation.models import GenerationError, GenerationRequest
from core.ai_generation.prompting import enhance_prompt
from core.ai_generation.providers import MockImageGenerationProvider
from core.ai_generation.queue import GenerationWorker
from core.ai_generation.storage import GenerationHistoryStore, GenerationStorage
from core.playlist_manager import PlaylistEntry, PlaylistManager
from core.wallpaper_library import WallpaperLibrary


def make_request(simulate_error: str = "", quantity: int = 2, seed: int | None = 1234) -> GenerationRequest:
    prompt = "cidade futurista com neon azul e area limpa para icones"
    return GenerationRequest(
        prompt=prompt,
        enhanced_prompt=enhance_prompt(prompt, "cinematic", "texto, marca d'agua"),
        negative_prompt="texto, marca d'agua",
        style_id="cinematic",
        style_name="Cinematico",
        resolution=(640, 360),
        quantity=quantity,
        quality="fast",
        seed=seed,
        simulate_error=simulate_error,
    )


def assert_no_temp_left(storage: GenerationStorage) -> None:
    if not storage.temp_root.exists():
        return
    leftovers = [path for path in storage.temp_root.rglob("*") if path.exists()]
    assert not leftovers, f"temporary files left behind: {leftovers}"


def test_provider_and_storage(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "storage")
    history = GenerationHistoryStore(temp / "history.json")
    job_dir = storage.job_dir()
    progress_events: list[tuple[int, str]] = []
    result = provider.generate(make_request(), job_dir, lambda value, message: progress_events.append((value, message)), lambda: False)
    final_result = storage.post_process(result)
    storage.cleanup_job_dir(job_dir)
    assert len(final_result.images) == 2, "mock provider should return two images"
    assert progress_events, "progress events were not emitted"
    for image in final_result.images:
        loaded = QImage(str(image.path))
        assert not loaded.isNull(), f"invalid image: {image.path}"
        assert loaded.width() == 640 and loaded.height() == 360, "post-process resolution mismatch"
        assert not image.path.with_suffix(".png.tmp").exists(), "partial PNG was left behind"
    history.add_result(final_result)
    item = history.items()[0]
    assert item.negative_prompt == "texto, marca d'agua", "negative prompt not persisted"
    assert item.seed == 1234, "seed not persisted"
    assert_no_temp_left(storage)


def test_deterministic_seed(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "seed-storage")
    request = make_request(quantity=1, seed=None)
    first_job = storage.job_dir()
    second_job = storage.job_dir()
    first = provider.generate(request, first_job, lambda *_: None, lambda: False)
    second = provider.generate(request, second_job, lambda *_: None, lambda: False)
    storage.cleanup_job_dir(first_job)
    storage.cleanup_job_dir(second_job)
    assert first.images[0].seed == second.images[0].seed, "automatic seed must be deterministic"
    assert_no_temp_left(storage)


def test_provider_errors(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "error-storage")
    expected = {
        "auth": "auth",
        "rate_limit": "rate_limit",
        "timeout": "timeout",
        "unavailable": "provider_unavailable",
        "empty": "empty_result",
        "invalid": "invalid_image",
        "corrupt": "invalid_image",
        "save_failure": "save_failed",
        "permission_denied": "permission_denied",
        "disk_full": "disk_full",
        "malformed_metadata": "malformed_metadata",
    }
    for scenario, code in expected.items():
        job_dir = storage.job_dir()
        try:
            provider.generate(make_request(scenario, 1), job_dir, lambda *_: None, lambda: False)
        except GenerationError as exc:
            assert exc.code.value == code, f"{scenario}: expected {code}, got {exc.code.value}"
        else:
            raise AssertionError(f"{scenario}: simulated provider error did not fail")
        finally:
            storage.cleanup_job_dir(job_dir)
    assert_no_temp_left(storage)


def test_cancellation_and_worker_cleanup(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "worker-storage")
    history = GenerationHistoryStore(temp / "worker-history.json")
    cancel_event = Event()
    cancel_event.set()
    worker = GenerationWorker(provider, storage, history, make_request(quantity=1), cancel_event)
    seen: list[str] = []
    worker.cancelled.connect(seen.append)
    worker.run()
    assert seen, "worker did not emit cancellation"
    assert not history.items(), "cancelled jobs must not enter history"
    assert_no_temp_left(storage)


def test_history_delete_preserves_library(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "history-storage")
    history = GenerationHistoryStore(temp / "history-delete.json")
    job_dir = storage.job_dir()
    result = storage.post_process(provider.generate(make_request(quantity=1), job_dir, lambda *_: None, lambda: False))
    storage.cleanup_job_dir(job_dir)
    item = history.add_result(result)
    protected = {str(result.images[0].path)}
    assert history.delete_item(item.id, protected), "history item was not deleted"
    assert result.images[0].path.exists(), "protected library file was deleted"
    assert not history.items(), "history item remained after deletion"


def test_library_favorites_and_playlist(temp: Path) -> None:
    image = QImage(64, 36, QImage.Format.Format_RGB32)
    image.fill(0xFF336699)
    source = temp / "source.png"
    assert image.save(str(source), "PNG"), "test image save failed"
    library = WallpaperLibrary()
    library.personal_root = temp / "wallpapers"
    library.metadata_path = temp / "library.json"
    library.personal_root.mkdir(parents=True, exist_ok=True)
    library._metadata = {"favorites": [], "recent": [], "details": {}}
    imported = library.import_files([source])
    assert imported, "library import failed"
    library.update_details(imported[0], ["ia", "mock"], "Criados com IA", "leve")
    assert library.toggle_favorite(imported[0]), "favorite was not enabled"
    assert library.items()[0].favorite, "favorite did not persist"
    playlists = PlaylistManager(temp / "playlists.json")
    playlists.save("default", [PlaylistEntry(str(imported[0].path), 60)])
    presentation = playlists.presentation_for(playlists.entries("default")[0])
    assert presentation and presentation["renderer"] == "image", "playlist presentation failed"


def main() -> int:
    app = QApplication.instance() or QApplication([])
    temp = Path(tempfile.mkdtemp(prefix="movaura-ai-test-"))
    try:
        test_provider_and_storage(temp)
        test_deterministic_seed(temp)
        test_provider_errors(temp)
        test_cancellation_and_worker_cleanup(temp)
        test_history_delete_preserves_library(temp)
        test_library_favorites_and_playlist(temp)
        print("ai_generation_tests=ok")
        return 0
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
