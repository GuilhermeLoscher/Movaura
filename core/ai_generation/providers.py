from __future__ import annotations

import errno
import hashlib
import logging
import random
import time
import uuid
from pathlib import Path
from typing import Callable, Protocol

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPen

from core.ai_generation.models import (
    GenerationError,
    GenerationErrorCode,
    GenerationImage,
    GenerationRequest,
    GenerationResult,
    ProviderCapabilities,
)
from core.ai_generation.prompting import style_by_id


ProgressCallback = Callable[[int, str], None]
CancelCallback = Callable[[], bool]
logger = logging.getLogger(__name__)


class ImageGenerationProvider(Protocol):
    """Provider contract for image generation backends.

    Real network providers must enforce their own request timeouts, regularly
    honor ``should_cancel`` during long calls, and map provider/storage failures
    to ``GenerationError`` instead of leaking technical exceptions to the UI.
    """

    @property
    def capabilities(self) -> ProviderCapabilities:
        ...

    def generate(
        self,
        request: GenerationRequest,
        output_dir: Path,
        progress: ProgressCallback,
        should_cancel: CancelCallback,
    ) -> GenerationResult:
        ...


class MockImageGenerationProvider:
    """Deterministic local provider used until real cloud providers are added."""

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            name="mock",
            display_name="Mock local sem custo",
            mock=True,
            max_images=4,
        )

    def generate(
        self,
        request: GenerationRequest,
        output_dir: Path,
        progress: ProgressCallback,
        should_cancel: CancelCallback,
    ) -> GenerationResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        self._simulate_error_if_requested(request.simulate_error, "before")
        quantity = max(1, min(request.quantity, self.capabilities.max_images))
        width, height = request.resolution
        base_seed = request.seed if request.seed is not None else self._stable_seed(request)
        images: list[GenerationImage] = []

        for index in range(quantity):
            self._raise_if_cancelled(should_cancel, "Cancellation requested by user.")
            percent = int(index / quantity * 70)
            progress(percent, f"Gerando variacao {index + 1} de {quantity}...")
            self._sleep_with_cancel(request.quality, should_cancel)
            seed = base_seed + index * 9973
            path = output_dir / f"movaura-ai-{seed}-{index + 1}.png"
            self._simulate_error_if_requested(request.simulate_error, "during", path)
            returned_invalid = self._write_invalid_provider_return(request.simulate_error, path)
            if not returned_invalid:
                self._render_mock_wallpaper(request, path, width, height, seed)
            if not returned_invalid and QImage(str(path)).isNull():
                raise GenerationError(
                    GenerationErrorCode.INVALID_IMAGE,
                    "A imagem gerada nao pode ser validada.",
                    str(path),
                )
            images.append(
                GenerationImage(
                    path=path,
                    width=width,
                    height=height,
                    seed=seed,
                    prompt=request.final_prompt,
                    metadata={"mock": True, "variation": index + 1},
                )
            )

        self._simulate_error_if_requested(request.simulate_error, "after")
        if not images:
            raise GenerationError(
                GenerationErrorCode.EMPTY_RESULT,
                "O provedor nao retornou imagens.",
            )
        progress(100, "Geracao concluida.")
        return GenerationResult(
            provider_id=self.capabilities.name,
            request=request,
            images=images,
            metadata={"mock": True},
        )

    @staticmethod
    def _sleep_with_cancel(quality: str, should_cancel: CancelCallback) -> None:
        duration = {"fast": 0.25, "recommended": 0.45, "max": 0.7}.get(quality, 0.45)
        steps = max(2, int(duration / 0.05))
        for _ in range(steps):
            MockImageGenerationProvider._raise_if_cancelled(
                should_cancel,
                "Cancellation requested while waiting.",
            )
            time.sleep(duration / steps)

    @staticmethod
    def _raise_if_cancelled(should_cancel: CancelCallback, technical_message: str) -> None:
        if should_cancel():
            raise GenerationError(
                GenerationErrorCode.CANCELLED,
                "Geracao cancelada.",
                technical_message,
            )

    @staticmethod
    def _stable_seed(request: GenerationRequest) -> int:
        source = "|".join(
            [
                request.final_prompt,
                request.negative_prompt,
                request.style_id,
                f"{request.resolution[0]}x{request.resolution[1]}",
                request.quality,
            ]
        )
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        return int(digest[:12], 16) % 1_000_000_000

    @staticmethod
    def _simulate_error_if_requested(value: str, stage: str, path: Path | None = None) -> None:
        code = value.strip().lower()
        if not code or code == "none":
            return
        mapping = {
            "auth": (GenerationErrorCode.AUTH, "A chave do provedor foi recusada."),
            "rate_limit": (GenerationErrorCode.RATE_LIMIT, "O limite de geracoes foi atingido."),
            "timeout": (GenerationErrorCode.TIMEOUT, "O provedor demorou demais para responder."),
            "unavailable": (GenerationErrorCode.PROVIDER_UNAVAILABLE, "O provedor esta indisponivel agora."),
            "empty": (GenerationErrorCode.EMPTY_RESULT, "Nenhuma imagem foi retornada."),
        }
        if code in mapping and stage == "before":
            error_code, message = mapping[code]
            raise GenerationError(error_code, message, f"Mock simulated error: {code}")
        if stage == "during" and path:
            if code in {"invalid", "provider_error_invalid"}:
                raise GenerationError(
                    GenerationErrorCode.INVALID_IMAGE,
                    "O provedor informou que a imagem retornada e invalida.",
                    str(path),
                )
            if code == "save_failure":
                target = path.parent
                image = QImage(16, 16, QImage.Format.Format_RGB32)
                image.fill(QColor("#000000"))
                if not image.save(str(target), "PNG"):
                    raise GenerationError(
                        GenerationErrorCode.SAVE_FAILED,
                        "Nao foi possivel salvar a imagem gerada.",
                        f"QImage.save returned false for {target}",
                    )
            if code == "permission_denied":
                raise GenerationError(
                    GenerationErrorCode.PERMISSION_DENIED,
                    "Sem permissao para gravar a imagem gerada.",
                    f"{PermissionError(errno.EACCES, 'permission denied', str(path))}",
                )
            if code == "disk_full":
                raise GenerationError(
                    GenerationErrorCode.DISK_FULL,
                    "Sem espaco suficiente para salvar a imagem gerada.",
                    f"{OSError(errno.ENOSPC, 'no space left on device', str(path))}",
                )
            if code == "malformed_metadata":
                raise GenerationError(
                    GenerationErrorCode.MALFORMED_METADATA,
                    "O provedor retornou metadados invalidos.",
                    "Mock metadata payload is malformed.",
                )
        if code == "invalid" and stage == "after":
            raise GenerationError(
                GenerationErrorCode.INVALID_IMAGE,
                "A imagem retornada falhou na validacao.",
                "Mock simulated invalid image.",
            )

    @staticmethod
    def _write_invalid_provider_return(value: str, path: Path) -> bool:
        code = value.strip().lower()
        if code == "returned_invalid_image":
            path.write_text("isto nao e uma imagem png", encoding="utf-8")
            return True
        if code in {"corrupt", "returned_corrupt_image"}:
            path.write_bytes(b"\x89PNG\r\n\x1a\ncorrompido")
            return True
        return False

    @staticmethod
    def _render_mock_wallpaper(
        request: GenerationRequest,
        path: Path,
        width: int,
        height: int,
        seed: int,
    ) -> None:
        style = style_by_id(request.style_id)
        randomizer = random.Random(seed)
        image = QImage(width, height, QImage.Format.Format_RGB32)
        image.fill(QColor(style.palette[0]))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0.0, QColor(style.palette[0]))
        gradient.setColorAt(0.52, QColor(style.palette[1]))
        gradient.setColorAt(1.0, QColor(style.palette[2]))
        painter.fillRect(0, 0, width, height, gradient)

        for layer in range(28):
            alpha = randomizer.randint(28, 120)
            color = QColor(randomizer.choice(style.palette))
            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            size = randomizer.randint(max(24, width // 40), max(90, width // 8))
            x = randomizer.randint(-size, width)
            y = randomizer.randint(-size, height)
            if layer % 3 == 0:
                painter.drawEllipse(x, y, size, size)
            else:
                rect = QRectF(x, y, size * 1.8, size * 0.5)
                painter.save()
                painter.translate(rect.center())
                painter.rotate(randomizer.randint(-35, 35))
                painter.translate(-rect.center())
                painter.drawRoundedRect(rect, 18, 18)
                painter.restore()

        safe_area = QRectF(width * 0.08, height * 0.74, width * 0.84, height * 0.18)
        painter.setPen(QPen(QColor(255, 255, 255, 70), max(1, width // 650)))
        painter.setBrush(QColor(0, 0, 0, 50))
        painter.drawRoundedRect(safe_area, 18, 18)
        painter.setPen(QColor(255, 255, 255, 190))
        font = QFont("Segoe UI", max(12, min(24, width // 72)))
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        prompt = request.prompt.strip() or "Movaura AI"
        if len(prompt) > 110:
            prompt = prompt[:107].rstrip() + "..."
        painter.drawText(
            safe_area.adjusted(22, 14, -22, -14),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap,
            prompt,
        )
        painter.end()
        MockImageGenerationProvider._save_png_atomic(image, path)

    @staticmethod
    def _save_png_atomic(image: QImage, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            if not image.save(str(temporary), "PNG"):
                raise GenerationError(
                    GenerationErrorCode.SAVE_FAILED,
                    "Nao foi possivel salvar a imagem gerada.",
                    f"QImage.save returned false for {temporary}",
                )
            if QImage(str(temporary)).isNull():
                raise GenerationError(
                    GenerationErrorCode.INVALID_IMAGE,
                    "A imagem gerada nao pode ser validada.",
                    str(temporary),
                )
            temporary.replace(path)
        except PermissionError as exc:
            raise GenerationError(
                GenerationErrorCode.PERMISSION_DENIED,
                "Sem permissao para salvar a imagem gerada.",
                str(exc),
            ) from exc
        except OSError as exc:
            code = GenerationErrorCode.DISK_FULL if exc.errno == errno.ENOSPC else GenerationErrorCode.SAVE_FAILED
            message = (
                "Sem espaco suficiente para salvar a imagem gerada."
                if code == GenerationErrorCode.DISK_FULL
                else "Nao foi possivel salvar a imagem gerada."
            )
            raise GenerationError(code, message, str(exc)) from exc
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError as exc:
                logger.warning("Could not remove temporary AI provider file %s: %s", temporary, exc)
