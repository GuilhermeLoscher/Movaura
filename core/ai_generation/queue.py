from __future__ import annotations

import logging
from pathlib import Path
from threading import Event

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from core.ai_generation.models import GenerationError, GenerationErrorCode, GenerationRequest, GenerationResult, GenerationState
from core.ai_generation.providers import ImageGenerationProvider
from core.ai_generation.storage import GenerationHistoryStore, GenerationStorage


logger = logging.getLogger(__name__)


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
        terminal_emitted = False
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
                logger.exception("Nao foi possivel registrar sucesso da geracao no historico.")
                rollback_warnings = self.storage.remove_result(final_result)
                technical = [f"history.add_result failed: {type(exc).__name__}: {exc}"]
                if rollback_warnings:
                    technical.append("rollback warnings: " + " | ".join(rollback_warnings))
                raise GenerationError(
                    GenerationErrorCode.SAVE_FAILED,
                    "Nao foi possivel salvar o historico da geracao.",
                    " ; ".join(technical),
                ) from exc
            self.state_changed.emit(GenerationState.COMPLETED.value, "Wallpaper gerado.")
            self.completed.emit(final_result)
            terminal_emitted = True
        except GenerationError as exc:
            if exc.code == GenerationErrorCode.CANCELLED:
                self.state_changed.emit(GenerationState.CANCELLED.value, exc.user_message)
                self.cancelled.emit(exc.user_message)
                terminal_emitted = True
            else:
                exc = self._with_failure_history_attempt(exc)
                self.state_changed.emit(GenerationState.FAILED.value, exc.user_message)
                self.failed.emit(exc)
                terminal_emitted = True
        except Exception as exc:
            error = GenerationError(
                GenerationErrorCode.UNKNOWN,
                "Nao foi possivel gerar o wallpaper.",
                f"{type(exc).__name__}: {exc}",
            )
            error = self._with_failure_history_attempt(error)
            self.state_changed.emit(GenerationState.FAILED.value, error.user_message)
            self.failed.emit(error)
            terminal_emitted = True
        finally:
            try:
                self.storage.cleanup_job_dir(output_dir)
            except Exception as exc:
                logger.exception("Nao foi possivel limpar temporarios da geracao de IA.")
                if not terminal_emitted:
                    fallback = GenerationError(
                        GenerationErrorCode.SAVE_FAILED,
                        "Nao foi possivel finalizar a geracao.",
                        f"cleanup_job_dir failed: {type(exc).__name__}: {exc}",
                    )
                    self.state_changed.emit(GenerationState.FAILED.value, fallback.user_message)
                    self.failed.emit(fallback)
                    terminal_emitted = True
            if not terminal_emitted:
                fallback = GenerationError(
                    GenerationErrorCode.UNKNOWN,
                    "Nao foi possivel finalizar a geracao.",
                    "Worker exited without a terminal signal.",
                )
                logger.error("AI generation worker exited without terminal signal.")
                self.state_changed.emit(GenerationState.FAILED.value, fallback.user_message)
                self.failed.emit(fallback)

    def _with_failure_history_attempt(self, error: GenerationError) -> GenerationError:
        try:
            self.history.add_failure(self.request, error.user_message)
            return error
        except Exception as history_exc:
            logger.exception("Nao foi possivel registrar a falha da geracao no historico.")
            technical = error.technical_message
            suffix = f"history.add_failure failed: {type(history_exc).__name__}: {history_exc}"
            technical = f"{technical} ; {suffix}" if technical else suffix
            return GenerationError(error.code, error.user_message, technical)


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
        self._finishing = False

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
        logger.warning("AI generation thread exceeded shutdown timeout of %s ms.", timeout_ms)
        if second_timeout_ms > 0 and self._wait_for_thread(second_timeout_ms):
            self._clear_refs()
            return True
        return False

    def _start_now(self, request: GenerationRequest) -> None:
        self._finishing = False
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
        if self._finishing:
            return
        self._finishing = True
        if self._wait_for_thread(3000):
            self._clear_refs()
            return
        logger.warning("AI generation thread did not finish after terminal signal.")
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
        self._finishing = False
