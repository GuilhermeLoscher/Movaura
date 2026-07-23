from __future__ import annotations

from pathlib import Path

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
    ) -> None:
        super().__init__()
        self.provider = provider
        self.storage = storage
        self.history = history
        self.request = request
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            self.state_changed.emit(GenerationState.ENHANCING_PROMPT.value, "Preparando prompt...")
            self.progress.emit(4, "Prompt pronto.")
            output_dir: Path = self.storage.job_dir()
            self.state_changed.emit(GenerationState.GENERATING.value, "Gerando wallpaper...")
            result = self.provider.generate(self.request, output_dir, self.progress.emit, lambda: self._cancelled)
            if self._cancelled:
                raise GenerationError(GenerationErrorCode.CANCELLED, "Geracao cancelada.")
            self.state_changed.emit(GenerationState.POST_PROCESSING.value, "Finalizando imagem...")
            final_result = self.storage.post_process(result)
            if not final_result.images:
                raise GenerationError(GenerationErrorCode.EMPTY_RESULT, "Nenhuma imagem valida foi gerada.")
            self.history.add_result(final_result)
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

    @property
    def is_running(self) -> bool:
        return self.thread is not None and self.thread.isRunning()

    def start(self, request: GenerationRequest) -> bool:
        if self.is_running:
            return False
        self.thread = QThread()
        self.worker = GenerationWorker(self.provider, self.storage, self.history, request)
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
        self.thread.finished.connect(self.thread.deleteLater)
        self.state_changed.emit(GenerationState.QUEUED.value, "Geracao colocada na fila.")
        self.thread.start()
        return True

    def cancel(self) -> None:
        if self.worker:
            self.worker.cancel()

    def _finish(self, *_args: object) -> None:
        if self.thread:
            self.thread.quit()
            self.thread.wait(3000)
        if self.worker:
            self.worker.deleteLater()
        self.worker = None
        self.thread = None
