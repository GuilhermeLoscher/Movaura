from __future__ import annotations

import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage

from core.ai_generation.models import (
    GenerationError,
    GenerationErrorCode,
    GenerationHistoryItem,
    GenerationImage,
    GenerationRequest,
    GenerationResult,
)
from core.json_store import read_json_object, write_json_atomic
from core.runtime_paths import data_root


class GenerationStorage:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or data_root() / "ai_generation"
        self.temp_root = self.root / "temp"
        self.final_root = self.root / "results"
        self.final_root.mkdir(parents=True, exist_ok=True)

    def job_dir(self) -> Path:
        path = self.temp_root / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def post_process(self, result: GenerationResult) -> GenerationResult:
        final_images: list[GenerationImage] = []
        created_paths: list[Path] = []
        for index, image in enumerate(result.images, start=1):
            final_path = self._available_path(result.request, image.seed, index)
            processed = self._fit_to_resolution(image.path, result.request.resolution)
            if processed.isNull():
                self._remove_paths(created_paths)
                raise GenerationError(
                    GenerationErrorCode.INVALID_IMAGE,
                    "A imagem gerada nao pode ser validada.",
                    str(image.path),
                )
            try:
                self._save_png_atomic(processed, final_path)
                created_paths.append(final_path)
                final_images.append(
                    GenerationImage(
                        path=final_path,
                        width=result.request.resolution[0],
                        height=result.request.resolution[1],
                        seed=image.seed,
                        prompt=image.prompt,
                        metadata=dict(image.metadata),
                    )
                )
            except Exception:
                self._remove_paths(created_paths)
                raise
        return GenerationResult(
            provider_id=result.provider_id,
            request=result.request,
            images=final_images,
            metadata=dict(result.metadata),
        )

    @staticmethod
    def cleanup_job_dir(path: Path | None) -> None:
        if path and path.exists():
            parent = path.parent
            shutil.rmtree(path, ignore_errors=True)
            try:
                parent.rmdir()
            except OSError:
                pass

    def _available_path(self, request: GenerationRequest, seed: int, index: int) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base = self._slug(request.prompt or request.style_name)
        path = self.final_root / f"{stamp}-{base}-{seed}-{index}.png"
        if not path.exists():
            return path
        for number in range(2, 1000):
            candidate = self.final_root / f"{stamp}-{base}-{seed}-{index}-{number}.png"
            if not candidate.exists():
                return candidate
        raise OSError("Nao foi possivel criar nome livre para imagem gerada.")

    @staticmethod
    def _fit_to_resolution(path: Path, resolution: tuple[int, int]) -> QImage:
        image = QImage(str(path))
        if image.isNull():
            return image
        target_width, target_height = resolution
        scaled = image.scaled(
            target_width,
            target_height,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        left = max(0, (scaled.width() - target_width) // 2)
        top = max(0, (scaled.height() - target_height) // 2)
        return scaled.copy(left, top, target_width, target_height)

    @staticmethod
    def _save_png_atomic(image: QImage, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f"{path.suffix}.tmp")
        if temporary.exists():
            temporary.unlink()
        if not image.save(str(temporary), "PNG"):
            raise GenerationError(
                GenerationErrorCode.SAVE_FAILED,
                "Nao foi possivel salvar a imagem final.",
                f"QImage.save returned false for {temporary}",
            )
        if QImage(str(temporary)).isNull():
            temporary.unlink(missing_ok=True)
            raise GenerationError(
                GenerationErrorCode.INVALID_IMAGE,
                "A imagem final nao passou na validacao.",
                str(temporary),
            )
        temporary.replace(path)

    @staticmethod
    def _remove_paths(paths: list[Path]) -> None:
        for path in paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    @staticmethod
    def _slug(text: str) -> str:
        cleaned = []
        for char in text.lower():
            if char.isalnum():
                cleaned.append(char)
            elif cleaned and cleaned[-1] != "-":
                cleaned.append("-")
        slug = "".join(cleaned).strip("-")[:42]
        return slug or "wallpaper"


class GenerationHistoryStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or data_root() / "ai_generation" / "history.json"

    def items(self) -> list[GenerationHistoryItem]:
        data = read_json_object(self.path) or {}
        raw_items = data.get("items", [])
        if not isinstance(raw_items, list):
            return []
        return [GenerationHistoryItem.from_json(item) for item in raw_items if isinstance(item, dict)]

    def add_result(self, result: GenerationResult, message: str = "Concluido") -> GenerationHistoryItem:
        request = result.request
        item = GenerationHistoryItem(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            provider_id=result.provider_id,
            prompt=request.prompt,
            enhanced_prompt=request.enhanced_prompt,
            style_id=request.style_id,
            style_name=request.style_name,
            resolution=f"{request.resolution[0]}x{request.resolution[1]}",
            quality=request.quality,
            images=[str(image.path) for image in result.images],
            status="completed",
            message=message,
            negative_prompt=request.negative_prompt,
            seed=result.images[0].seed if result.images else request.seed,
        )
        self._prepend(item)
        return item

    def add_failure(self, request: GenerationRequest, message: str) -> GenerationHistoryItem:
        item = GenerationHistoryItem(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            provider_id=request.provider_id,
            prompt=request.prompt,
            enhanced_prompt=request.enhanced_prompt,
            style_id=request.style_id,
            style_name=request.style_name,
            resolution=f"{request.resolution[0]}x{request.resolution[1]}",
            quality=request.quality,
            images=[],
            status="failed",
            message=message,
            negative_prompt=request.negative_prompt,
            seed=request.seed,
        )
        self._prepend(item)
        return item

    def delete_item(self, item_id: str, protected_paths: set[str] | None = None) -> bool:
        current = self.items()
        target = next((item for item in current if item.id == item_id), None)
        if target is None:
            return False
        protected = {str(Path(path).resolve()).lower() for path in (protected_paths or set())}
        remaining = [item for item in current if item.id != item_id]
        referenced = {path for item in remaining for path in item.images}
        for raw_path in target.images:
            normalized = str(Path(raw_path).resolve()).lower()
            if raw_path not in referenced and normalized not in protected:
                try:
                    Path(raw_path).unlink(missing_ok=True)
                except OSError:
                    pass
        write_json_atomic(self.path, {"items": [entry.to_json() for entry in remaining]})
        return True

    def _prepend(self, item: GenerationHistoryItem) -> None:
        current = [item, *self.items()][:120]
        write_json_atomic(self.path, {"items": [entry.to_json() for entry in current]})
