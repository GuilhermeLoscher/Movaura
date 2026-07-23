from __future__ import annotations

import shutil
import sys
import tempfile
import errno
from pathlib import Path
from threading import Event

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtCore import QEventLoop, QThread, QTimer
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication

from core.ai_generation.models import GenerationError, GenerationErrorCode, GenerationImage, GenerationRequest, GenerationResult
from core.ai_generation.prompting import enhance_prompt
from core.ai_generation.providers import MockImageGenerationProvider
from core.ai_generation.queue import GenerationQueue, GenerationWorker
from core.ai_generation.storage import GenerationHistoryStore, GenerationStorage
from core.json_store import write_json_atomic
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


def wait_until(condition, timeout_ms: int = 5000) -> bool:
    app = QApplication.instance() or QApplication([])
    if condition():
        return True
    loop = QEventLoop()
    poll = QTimer()
    poll.setInterval(25)
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.setInterval(timeout_ms)

    def check() -> None:
        if condition():
            poll.stop()
            timeout.stop()
            loop.quit()

    poll.timeout.connect(check)
    timeout.timeout.connect(loop.quit)
    poll.start()
    timeout.start()
    loop.exec()
    app.processEvents()
    return bool(condition())


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
        "provider_error_invalid": "invalid_image",
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


def test_returned_invalid_images_are_detected_by_storage(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "returned-invalid-storage")
    for scenario in ("returned_invalid_image", "returned_corrupt_image", "corrupt"):
        job_dir = storage.job_dir()
        result = provider.generate(make_request(scenario, 1), job_dir, lambda *_: None, lambda: False)
        try:
            storage.post_process(result)
        except GenerationError as exc:
            assert exc.code == GenerationErrorCode.INVALID_IMAGE, f"{scenario}: expected invalid_image, got {exc.code}"
        else:
            raise AssertionError(f"{scenario}: invalid provider file reached final storage")
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


def test_generation_queue_qthread_lifecycle(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "queue-storage")
    history = GenerationHistoryStore(temp / "queue-history.json", storage.final_root)
    queue = GenerationQueue(provider, storage, history)
    completed: list[object] = []
    cancelled: list[str] = []
    states: list[str] = []
    queue.completed.connect(completed.append)
    queue.cancelled.connect(cancelled.append)
    queue.state_changed.connect(lambda state, _message: states.append(state))
    assert queue.start(make_request(quantity=1, seed=10)), "first queued job did not start"
    assert not queue.start(make_request(quantity=1, seed=11)), "queue must reject hidden pending jobs"
    assert wait_until(lambda: completed and not queue.is_running), "QThread job did not complete"
    assert len(history.items()) == 1, "completed queue job did not enter history"
    assert not cancelled, "completed job emitted cancellation"
    assert_no_temp_left(storage)


def test_generation_queue_cancel_and_shutdown(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "queue-cancel-storage")
    history = GenerationHistoryStore(temp / "queue-cancel-history.json", storage.final_root)
    queue = GenerationQueue(provider, storage, history)
    cancelled: list[str] = []
    queue.cancelled.connect(cancelled.append)
    assert queue.start(make_request(quantity=1, seed=12, simulate_error="",)), "cancel job did not start"
    queue.cancel()
    assert wait_until(lambda: cancelled and not queue.is_running), "cancelled QThread job did not stop"
    assert not history.items(), "cancelled QThread job entered history"
    assert queue.shutdown(), "shutdown after cancellation should be clean"
    assert_no_temp_left(storage)


def test_generation_queue_shutdown_timeout_keeps_refs(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "queue-timeout-storage")
    history = GenerationHistoryStore(temp / "queue-timeout-history.json", storage.final_root)
    queue = GenerationQueue(provider, storage, history)
    fake_thread = QThread()
    queue.thread = fake_thread
    queue._wait_for_thread = lambda _timeout: False  # type: ignore[method-assign]
    assert not queue.shutdown(1, 0), "shutdown timeout must return false"
    assert queue.thread is fake_thread, "timed-out shutdown discarded thread reference"


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


def test_history_retention_deletes_only_safe_orphans(temp: Path) -> None:
    storage = GenerationStorage(temp / "retention-storage")
    history = GenerationHistoryStore(temp / "retention.json", storage.final_root)
    protected_outside = temp / "outside.png"
    protected_outside.write_bytes(b"outside")
    old_inside = storage.final_root / "old-inside.png"
    old_inside.parent.mkdir(parents=True, exist_ok=True)
    old_inside.write_bytes(b"old")
    write_json_atomic(temp / "library.json", {"details": {str(protected_outside): {"tags": ["ia"]}}})

    def result_for(path: Path, index: int) -> GenerationResult:
        request = make_request(quantity=1, seed=index)
        image = GenerationImage(path=path, width=640, height=360, seed=index, prompt=request.final_prompt)
        return GenerationResult("mock", request, [image])

    history.add_result(result_for(old_inside, 1))
    history.add_result(result_for(protected_outside, 2), protected_paths={str(protected_outside)})
    for index in range(3, 124):
        image_path = storage.final_root / f"new-{index}.png"
        image_path.write_bytes(b"new")
        history.add_result(result_for(image_path, index), protected_paths={str(protected_outside)})
    assert len(history.items()) == 120, "history retention limit was not enforced"
    assert not old_inside.exists(), "unreferenced AI result inside root was not cleaned"
    assert protected_outside.exists(), "protected outside path was deleted"


def test_storage_failure_mapping_and_rollbacks(temp: Path) -> None:
    storage = GenerationStorage(temp / "failure-storage")
    job_dir = storage.job_dir()
    image = QImage(64, 36, QImage.Format.Format_RGB32)
    image.fill(0xFF112233)
    source = job_dir / "source.png"
    assert image.save(str(source), "PNG")
    request = make_request(quantity=1, seed=44)
    generated = GenerationImage(source, 640, 360, 44, request.final_prompt)
    result = GenerationResult("mock", request, [generated])

    storage.save_image = lambda _image, _path: False
    try:
        storage.post_process(result)
    except GenerationError as exc:
        assert exc.code == GenerationErrorCode.SAVE_FAILED, "save false was not mapped to SAVE_FAILED"
    else:
        raise AssertionError("save false did not fail")
    assert not list(storage.final_root.glob("*.tmp")), "temporary file leaked after save false"

    storage.save_image = lambda image_obj, path: image_obj.save(str(path), "PNG")

    def deny_replace(_temporary: Path, _final: Path) -> None:
        raise PermissionError(errno.EACCES, "denied")

    storage.replace_file = deny_replace
    try:
        storage.post_process(result)
    except GenerationError as exc:
        assert exc.code == GenerationErrorCode.PERMISSION_DENIED, "PermissionError was not mapped"
    else:
        raise AssertionError("PermissionError replace did not fail")

    def disk_full_replace(_temporary: Path, _final: Path) -> None:
        raise OSError(errno.ENOSPC, "full")

    storage.replace_file = disk_full_replace
    try:
        storage.post_process(result)
    except GenerationError as exc:
        assert exc.code == GenerationErrorCode.DISK_FULL, "ENOSPC was not mapped"
    else:
        raise AssertionError("ENOSPC replace did not fail")
    assert not list(storage.final_root.glob("*.tmp")), "temporary file leaked after replace failure"
    storage.cleanup_job_dir(job_dir)


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
        test_returned_invalid_images_are_detected_by_storage(temp)
        test_cancellation_and_worker_cleanup(temp)
        test_generation_queue_qthread_lifecycle(temp)
        test_generation_queue_cancel_and_shutdown(temp)
        test_generation_queue_shutdown_timeout_keeps_refs(temp)
        test_history_delete_preserves_library(temp)
        test_history_retention_deletes_only_safe_orphans(temp)
        test_storage_failure_mapping_and_rollbacks(temp)
        test_library_favorites_and_playlist(temp)
        print("ai_generation_tests=ok")
        return 0
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
