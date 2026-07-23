from __future__ import annotations

from pathlib import Path
from threading import Event

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from core.ai_generation.models import GenerationError, GenerationErrorCode, GenerationRequest, GenerationResult, GenerationState
from core.ai_generation.providers import ImageGenerationProvider
from core.ai_generation.storage import GenerationHistoryStore, GenerationStorage


class GenerationWorker(QObject):
    progress = pyqtSignal(int, str)
    state_changed = pyqtSignal(str, str)
    completed = pyqtSignal(object)
    failed = pyqtSignal(object)
    cancelled = pyqtSignal(str)

    def __init__(
        self,
        provider: ImageGenerationProvider,
        storage: GenerationStorage,
        history: GenerationHistoryStore,
        request: GenerationRequest,
        cancel_event: Event,
    ) -> None:
        super().__init__()
        self.provider = provider
        self.storage = storage
        self.history = history
        self.request = request
        self.cancel_event = cancel_event

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        output_dir: Path | None = None
        try:
            self.state_changed.emit(GenerationState.ENHANCING_PROMPT.value, "Preparando prompt...")
            self.progress.emit(4, "Prompt pronto.")
            output_dir = self.storage.job_dir()
            self.state_changed.emit(GenerationState.GENERATING.value, "Gerando wallpaper...")
            result = self.provider.generate(self.request, output_dir, self.progress.emit, self.cancel_event.is_set)
            if self.cancel_event.is_set():
                raise GenerationError(GenerationErrorCode.CANCELLED, "Geracao cancelada.")
            self.state_changed.emit(GenerationState.POST_PROCESSING.value, "Finalizando imagem...")
            final_result = self.storage.post_process(result)
            if not final_result.images:
                raise GenerationError(GenerationErrorCode.EMPTY_RESULT, "Nenhuma imagem valida foi gerada.")
            try:
                self.history.add_result(final_result)
            except Exception as exc:
                self.storage.remove_result(final_result)
                raise GenerationError(
                    GenerationErrorCode.SAVE_FAILED,
                    "Nao foi possivel salvar o historico da geracao.",
                    f"{type(exc).__name__}: {exc}",
                ) from exc
            self.state_changed.emit(GenerationState.COMPLETED.value, "Wallpaper gerado.")
            self.completed.emit(final_result)
        except GenerationError as exc:
            if exc.code == GenerationErrorCode.CANCELLED:
                self.state_changed.emit(GenerationState.CANCELLED.value, exc.user_message)
                self.cancelled.emit(exc.user_message)
            else:
                self.history.add_failure(self.request, exc.user_message)
                self.state_changed.emit(GenerationState.FAILED.value, exc.user_message)
                self.failed.emit(exc)
        except Exception as exc:
            error = GenerationError(
                GenerationErrorCode.UNKNOWN,
                "Nao foi possivel gerar o wallpaper.",
                f"{type(exc).__name__}: {exc}",
            )
            self.history.add_failure(self.request, error.user_message)
            self.state_changed.emit(GenerationState.FAILED.value, error.user_message)
            self.failed.emit(error)
        finally:
            self.storage.cleanup_job_dir(output_dir)


class GenerationQueue(QObject):
    progress = pyqtSignal(int, str)
    state_changed = pyqtSignal(str, str)
    completed = pyqtSignal(object)
    failed = pyqtSignal(object)
    cancelled = pyqtSignal(str)

    def __init__(
        self,
        provider: ImageGenerationProvider,
        storage: GenerationStorage,
        history: GenerationHistoryStore,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.provider = provider
        self.storage = storage
        self.history = history
        self.thread: QThread | None = None
        self.worker: GenerationWorker | None = None
        self.cancel_event: Event | None = None
        self._shutting_down = False

    @property
    def is_running(self) -> bool:
        return self.thread is not None and self.thread.isRunning()

    def start(self, request: GenerationRequest) -> bool:
        if self._shutting_down:
            return False
        if self.is_running:
            self.state_changed.emit(GenerationState.QUEUED.value, "Aguarde a geracao atual terminar antes de iniciar outra.")
            return False
        self._start_now(request)
        return True

    def cancel(self) -> None:
        if self.cancel_event:
            self.cancel_event.set()
        if self.worker:
            self.worker.cancel()

    def shutdown(self, timeout_ms: int = 5000, second_timeout_ms: int = 1500) -> bool:
        self._shutting_down = True
        self.cancel()
        if not self.thread:
            self._clear_refs()
            return True
        if self._wait_for_thread(timeout_ms):
            self._clear_refs()
            return True
        self.state_changed.emit(
            GenerationState.FAILED.value,
            "A geracao ainda esta encerrando. Aguarde alguns segundos antes de fechar o Movaura.",
        )
        if second_timeout_ms > 0 and self._wait_for_thread(second_timeout_ms):
            self._clear_refs()
            return True
        return False

    def _start_now(self, request: GenerationRequest) -> None:
        self.cancel_event = Event()
        self.thread = QThread()
        self.worker = GenerationWorker(self.provider, self.storage, self.history, request, self.cancel_event)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress)
        self.worker.state_changed.connect(self.state_changed)
        self.worker.completed.connect(self.completed)
        self.worker.failed.connect(self.failed)
        self.worker.cancelled.connect(self.cancelled)
        self.worker.completed.connect(self._finish)
        self.worker.failed.connect(self._finish)
        self.worker.cancelled.connect(self._finish)
        self.worker.completed.connect(self.worker.deleteLater)
        self.worker.failed.connect(self.worker.deleteLater)
        self.worker.cancelled.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.state_changed.emit(GenerationState.QUEUED.value, "Geracao colocada na fila.")
        self.thread.start()

    def _finish(self, *_args: object) -> None:
        if self._wait_for_thread(3000):
            self._clear_refs()
            return
        self.state_changed.emit(
            GenerationState.FAILED.value,
            "A thread de geracao nao encerrou dentro do tempo esperado.",
        )

    def _wait_for_thread(self, timeout_ms: int) -> bool:
        if not self.thread:
            return True
        if not self.thread.isRunning():
            return True
        self.thread.quit()
        return bool(self.thread.wait(timeout_ms))

    def _clear_refs(self) -> None:
        self.worker = None
        self.thread = None
        self.cancel_event = None
