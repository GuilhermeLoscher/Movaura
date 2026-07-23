from __future__ import annotations

import shutil
import sys
import tempfile
import errno
import time
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


class FailingHistoryStore(GenerationHistoryStore):
    def __init__(
        self,
        path: Path,
        results_root: Path,
        persistent_data_root: Path,
        fail_result: bool = False,
        fail_failure: bool = False,
    ) -> None:
        super().__init__(path, results_root, persistent_data_root)
        self.fail_result = fail_result
        self.fail_failure = fail_failure

    def add_result(self, result: GenerationResult, message: str = "Concluido", protected_paths: set[str] | None = None):
        if self.fail_result:
            raise PermissionError(errno.EACCES, "history result denied")
        return super().add_result(result, message, protected_paths)

    def add_failure(self, request: GenerationRequest, message: str, protected_paths: set[str] | None = None):
        if self.fail_failure:
            raise PermissionError(errno.EACCES, "history failure denied")
        return super().add_failure(request, message, protected_paths)


class UnexpectedFailureProvider(MockImageGenerationProvider):
    def generate(self, request, output_dir: Path, progress, should_cancel):
        output_dir.mkdir(parents=True, exist_ok=True)
        raise RuntimeError("unexpected provider failure")


class SlowCancelableProvider(MockImageGenerationProvider):
    def __init__(self, release_delay: float = 0.35) -> None:
        self.release_delay = release_delay

    def generate(self, request, output_dir: Path, progress, should_cancel):
        output_dir.mkdir(parents=True, exist_ok=True)
        progress(10, "Provider lento iniciado.")
        while not should_cancel():
            time.sleep(0.01)
        time.sleep(self.release_delay)
        raise GenerationError(GenerationErrorCode.CANCELLED, "Geracao cancelada.")


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


def run_queue_job(
    provider,
    storage: GenerationStorage,
    history: GenerationHistoryStore,
    request: GenerationRequest,
    timeout_ms: int = 5000,
) -> tuple[GenerationQueue, dict[str, list[object]]]:
    queue = GenerationQueue(provider, storage, history)
    signals: dict[str, list[object]] = {"completed": [], "failed": [], "cancelled": [], "states": []}
    queue.completed.connect(lambda result: signals["completed"].append(result))
    queue.failed.connect(lambda error: signals["failed"].append(error))
    queue.cancelled.connect(lambda message: signals["cancelled"].append(message))
    queue.state_changed.connect(lambda state, message: signals["states"].append((state, message)))
    assert queue.start(request), "queue job did not start"
    assert wait_until(lambda: terminal_count(signals) == 1 and not queue.is_running, timeout_ms), signals
    assert terminal_count(signals) == 1, f"expected one terminal signal, got {signals}"
    assert queue.thread is None and queue.worker is None, "queue references were not released"
    return queue, signals


def terminal_count(signals: dict[str, list[object]]) -> int:
    return len(signals["completed"]) + len(signals["failed"]) + len(signals["cancelled"])


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


def test_add_result_failure_add_failure_works_qthread(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "result-fail-storage")
    history = FailingHistoryStore(temp / "result-fail-history.json", storage.final_root, temp, fail_result=True)
    queue, signals = run_queue_job(provider, storage, history, make_request(quantity=1, seed=101))
    assert not signals["completed"] and signals["failed"] and not signals["cancelled"]
    assert len(history.items()) == 1 and history.items()[0].status == "failed", "failure history was not recorded"
    assert not list(storage.final_root.glob("*.png")), "final image was not rolled back"
    assert_no_temp_left(storage)
    assert queue.shutdown(), "shutdown after handled failure should return true"


def test_add_result_failure_add_failure_failure_qthread(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "double-history-fail-storage")
    history = FailingHistoryStore(
        temp / "double-history-fail.json",
        storage.final_root,
        temp,
        fail_result=True,
        fail_failure=True,
    )
    queue, signals = run_queue_job(provider, storage, history, make_request(quantity=1, seed=102))
    assert not signals["completed"] and len(signals["failed"]) == 1 and not signals["cancelled"]
    error = signals["failed"][0]
    assert isinstance(error, GenerationError)
    assert "history.add_result failed" in error.technical_message
    assert "history.add_failure failed" in error.technical_message
    assert not history.items(), "failed add_failure should not create history entries"
    assert not list(storage.final_root.glob("*.png")), "final image was not rolled back"
    assert_no_temp_left(storage)
    assert queue.start(make_request(quantity=1, seed=103)), "queue did not accept a new job after failed history"
    assert wait_until(lambda: not queue.is_running), "follow-up job did not finish"
    assert queue.shutdown(), "shutdown after double history failure should return true"


def test_add_result_failure_rollback_failure_add_failure_works_qthread(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "rollback-fail-storage")
    history = FailingHistoryStore(temp / "rollback-fail-history.json", storage.final_root, temp, fail_result=True)
    original_unlink = storage.unlink_file

    def fail_one(path: Path) -> None:
        if path.name.endswith("-2.png"):
            raise PermissionError(errno.EACCES, "rollback denied")
        original_unlink(path)

    storage.unlink_file = fail_one
    queue, signals = run_queue_job(provider, storage, history, make_request(quantity=2, seed=104))
    assert not signals["completed"] and len(signals["failed"]) == 1 and not signals["cancelled"]
    error = signals["failed"][0]
    assert isinstance(error, GenerationError)
    assert "history.add_result failed" in error.technical_message
    assert "rollback warnings" in error.technical_message
    assert storage.cleanup_warnings, "rollback warning was not recorded"
    remaining = list(storage.final_root.glob("*.png"))
    assert len(remaining) == 1 and remaining[0].name.endswith("-2.png"), "rollback failure was not explicit"
    assert len(history.items()) == 1 and history.items()[0].status == "failed", "failure was not recorded"
    assert_no_temp_left(storage)
    storage.unlink_file = original_unlink
    storage.remove_result(GenerationResult("mock", make_request(quantity=1), [GenerationImage(remaining[0], 1, 1, 1, "")]))


def test_add_result_failure_rollback_failure_add_failure_failure_qthread(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "all-secondary-fail-storage")
    history = FailingHistoryStore(
        temp / "all-secondary-fail-history.json",
        storage.final_root,
        temp,
        fail_result=True,
        fail_failure=True,
    )
    original_unlink = storage.unlink_file

    def fail_one(path: Path) -> None:
        if path.name.endswith("-2.png"):
            raise PermissionError(errno.EACCES, "rollback denied")
        original_unlink(path)

    storage.unlink_file = fail_one
    queue, signals = run_queue_job(provider, storage, history, make_request(quantity=2, seed=105))
    assert not signals["completed"] and len(signals["failed"]) == 1 and not signals["cancelled"]
    error = signals["failed"][0]
    assert isinstance(error, GenerationError)
    assert "history.add_result failed" in error.technical_message
    assert "rollback warnings" in error.technical_message
    assert "history.add_failure failed" in error.technical_message
    assert queue.thread is None and queue.worker is None
    assert queue.shutdown(), "shutdown should work after all secondary failure paths"
    storage.unlink_file = original_unlink
    for path in storage.final_root.glob("*.png"):
        path.unlink(missing_ok=True)
    assert_no_temp_left(storage)


def test_unexpected_provider_failure_add_failure_failure_qthread(temp: Path) -> None:
    provider = UnexpectedFailureProvider()
    storage = GenerationStorage(temp / "unexpected-storage")
    history = FailingHistoryStore(temp / "unexpected-history.json", storage.final_root, temp, fail_failure=True)
    _queue, signals = run_queue_job(provider, storage, history, make_request(quantity=1, seed=106))
    assert not signals["completed"] and len(signals["failed"]) == 1 and not signals["cancelled"]
    error = signals["failed"][0]
    assert isinstance(error, GenerationError)
    assert error.code == GenerationErrorCode.UNKNOWN
    assert "unexpected provider failure" in error.technical_message
    assert "history.add_failure failed" in error.technical_message
    assert_no_temp_left(storage)


def test_cancellation_with_failure_history_unavailable_qthread(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "cancel-history-unavailable-storage")
    history = FailingHistoryStore(temp / "cancel-history-unavailable.json", storage.final_root, temp, fail_failure=True)
    queue = GenerationQueue(provider, storage, history)
    signals: dict[str, list[object]] = {"completed": [], "failed": [], "cancelled": [], "states": []}
    queue.completed.connect(lambda result: signals["completed"].append(result))
    queue.failed.connect(lambda error: signals["failed"].append(error))
    queue.cancelled.connect(lambda message: signals["cancelled"].append(message))
    queue.state_changed.connect(lambda state, message: signals["states"].append((state, message)))
    assert queue.start(make_request(quantity=1, seed=107)), "cancel job did not start"
    queue.cancel()
    assert wait_until(lambda: terminal_count(signals) == 1 and not queue.is_running), signals
    assert not signals["completed"] and not signals["failed"] and len(signals["cancelled"]) == 1
    assert not history.items(), "cancelled job should not write failure history"
    assert_no_temp_left(storage)


def test_normal_success_single_terminal_qthread(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "success-storage")
    history = GenerationHistoryStore(temp / "success-history.json", storage.final_root, temp)
    _queue, signals = run_queue_job(provider, storage, history, make_request(quantity=1, seed=108))
    assert len(signals["completed"]) == 1 and not signals["failed"] and not signals["cancelled"]
    assert len(history.items()) == 1 and history.items()[0].status == "completed"
    final_images = list(storage.final_root.glob("*.png"))
    assert len(final_images) == 1 and not QImage(str(final_images[0])).isNull(), "success final image invalid"
    assert_no_temp_left(storage)


def test_real_shutdown_with_slow_thread(temp: Path) -> None:
    provider = SlowCancelableProvider(release_delay=0.35)
    storage = GenerationStorage(temp / "slow-shutdown-storage")
    history = GenerationHistoryStore(temp / "slow-shutdown-history.json", storage.final_root, temp)
    queue = GenerationQueue(provider, storage, history)
    assert queue.start(make_request(quantity=1, seed=109)), "slow job did not start"
    assert wait_until(lambda: queue.is_running, 1000), "slow thread did not start"
    assert not queue.shutdown(timeout_ms=20, second_timeout_ms=0), "short shutdown timeout should fail"
    assert queue.thread is not None, "short shutdown discarded thread reference"
    assert queue.shutdown(timeout_ms=1000, second_timeout_ms=500), "shutdown after provider release should succeed"
    assert queue.thread is None and queue.worker is None


def test_history_delete_preserves_library(temp: Path) -> None:
    provider = MockImageGenerationProvider()
    storage = GenerationStorage(temp / "history-storage")
    history = GenerationHistoryStore(temp / "history-delete.json", storage.final_root, temp)
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
    history = GenerationHistoryStore(temp / "retention.json", storage.final_root, temp)
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


def test_history_persistent_data_root_isolated(temp: Path) -> None:
    storage = GenerationStorage(temp / "isolated-storage")
    protected = storage.final_root / "protected.png"
    removable = storage.final_root / "removable.png"
    protected.parent.mkdir(parents=True, exist_ok=True)
    protected.write_bytes(b"protected")
    removable.write_bytes(b"removable")
    write_json_atomic(temp / "settings.json", {"media_path": str(protected)})
    history = GenerationHistoryStore(temp / "isolated-history.json", storage.final_root, temp)
    request = make_request(quantity=1)
    history.add_result(GenerationResult("mock", request, [GenerationImage(protected, 1, 1, 1, "")]))
    removed_item = history.add_result(GenerationResult("mock", request, [GenerationImage(removable, 1, 1, 2, "")]))
    assert history.delete_item(removed_item.id), "history delete failed"
    assert protected.exists(), "persistent settings path was not protected"
    assert not removable.exists(), "unprotected AI result was not removed"


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
        test_add_result_failure_add_failure_works_qthread(temp)
        test_add_result_failure_add_failure_failure_qthread(temp)
        test_add_result_failure_rollback_failure_add_failure_works_qthread(temp)
        test_add_result_failure_rollback_failure_add_failure_failure_qthread(temp)
        test_unexpected_provider_failure_add_failure_failure_qthread(temp)
        test_cancellation_with_failure_history_unavailable_qthread(temp)
        test_normal_success_single_terminal_qthread(temp)
        test_real_shutdown_with_slow_thread(temp)
        test_history_delete_preserves_library(temp)
        test_history_retention_deletes_only_safe_orphans(temp)
        test_history_persistent_data_root_isolated(temp)
        test_storage_failure_mapping_and_rollbacks(temp)
        test_library_favorites_and_playlist(temp)
        print("ai_generation_tests=ok")
        return 0
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
