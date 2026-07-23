from __future__ import annotations

import errno
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
from core.ai_generation.paths import is_inside_path, normalize_path
from core.json_store import read_json_object, write_json_atomic
from core.runtime_paths import data_root


class GenerationStorage:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or data_root() / "ai_generation"
        self.temp_root = self.root / "temp"
        self.final_root = self.root / "results"
        self.cleanup_warnings: list[str] = []
        self.save_image = lambda image, path: image.save(str(path), "PNG")
        self.replace_file = lambda temporary, final: temporary.replace(final)
        try:
            self.final_root.mkdir(parents=True, exist_ok=True)
        except PermissionError as exc:
            raise GenerationError(
                GenerationErrorCode.PERMISSION_DENIED,
                "Sem permissao para preparar a pasta de imagens da IA.",
                str(exc),
            ) from exc
        except OSError as exc:
            raise self._storage_error("Nao foi possivel preparar a pasta de imagens da IA.", exc) from exc

    def job_dir(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        path = self.temp_root / f"{stamp}-{uuid.uuid4().hex}"
        try:
            path.mkdir(parents=True, exist_ok=False)
        except PermissionError as exc:
            raise GenerationError(
                GenerationErrorCode.PERMISSION_DENIED,
                "Sem permissao para preparar os arquivos temporarios da IA.",
                str(exc),
            ) from exc
        except OSError as exc:
            raise self._storage_error("Nao foi possivel preparar os arquivos temporarios da IA.", exc) from exc
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

    def remove_result(self, result: GenerationResult) -> None:
        self._remove_paths([image.path for image in result.images])

    def cleanup_job_dir(self, path: Path | None) -> None:
        if path and path.exists():
            parent = path.parent
            try:
                shutil.rmtree(path)
            except OSError as exc:
                self._record_cleanup_warning(path, exc)
            try:
                parent.rmdir()
            except OSError as exc:
                if parent.exists() and not any(parent.iterdir()):
                    self._record_cleanup_warning(parent, exc)

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
        raise GenerationError(
            GenerationErrorCode.SAVE_FAILED,
            "Nao foi possivel criar um nome livre para a imagem gerada.",
            str(path),
        )

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

    def _save_png_atomic(self, image: QImage, path: Path) -> None:
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                raise GenerationError(
                    GenerationErrorCode.SAVE_FAILED,
                    "Ja existe uma imagem final com este nome.",
                    str(path),
                )
            if not self.save_image(image, temporary):
                raise GenerationError(
                    GenerationErrorCode.SAVE_FAILED,
                    "Nao foi possivel salvar a imagem final.",
                    f"QImage.save returned false for {temporary}",
                )
            if QImage(str(temporary)).isNull():
                raise GenerationError(
                    GenerationErrorCode.INVALID_IMAGE,
                    "A imagem final nao passou na validacao.",
                    str(temporary),
                )
            self.replace_file(temporary, path)
        except GenerationError:
            raise
        except PermissionError as exc:
            raise GenerationError(
                GenerationErrorCode.PERMISSION_DENIED,
                "Sem permissao para salvar a imagem final.",
                str(exc),
            ) from exc
        except OSError as exc:
            raise self._storage_error("Nao foi possivel salvar a imagem final.", exc) from exc
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError as exc:
                self._record_cleanup_warning(temporary, exc)

    def _remove_paths(self, paths: list[Path]) -> None:
        for path in paths:
            try:
                path.unlink(missing_ok=True)
            except OSError as exc:
                self._record_cleanup_warning(path, exc)

    @staticmethod
    def _storage_error(message: str, exc: OSError) -> GenerationError:
        if exc.errno == errno.ENOSPC:
            return GenerationError(GenerationErrorCode.DISK_FULL, "Sem espaco suficiente para salvar a imagem.", str(exc))
        return GenerationError(GenerationErrorCode.SAVE_FAILED, message, str(exc))

    def _record_cleanup_warning(self, path: Path, exc: OSError) -> None:
        self.cleanup_warnings.append(f"{path}: {exc}")

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
    MAX_ITEMS = 120

    def __init__(self, path: Path | None = None, results_root: Path | None = None) -> None:
        self.path = path or data_root() / "ai_generation" / "history.json"
        self.results_root = results_root or data_root() / "ai_generation" / "results"
        self.cleanup_warnings: list[str] = []

    def items(self) -> list[GenerationHistoryItem]:
        data = read_json_object(self.path) or {}
        raw_items = data.get("items", [])
        if not isinstance(raw_items, list):
            return []
        return [GenerationHistoryItem.from_json(item) for item in raw_items if isinstance(item, dict)]

    def add_result(
        self,
        result: GenerationResult,
        message: str = "Concluido",
        protected_paths: set[str] | None = None,
    ) -> GenerationHistoryItem:
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
        self._prepend(item, protected_paths)
        return item

    def add_failure(
        self,
        request: GenerationRequest,
        message: str,
        protected_paths: set[str] | None = None,
    ) -> GenerationHistoryItem:
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
        self._prepend(item, protected_paths)
        return item

    def delete_item(self, item_id: str, protected_paths: set[str] | None = None) -> bool:
        current = self.items()
        target = next((item for item in current if item.id == item_id), None)
        if target is None:
            return False
        remaining = [item for item in current if item.id != item_id]
        referenced = {normalize_path(path) for item in remaining for path in item.images}
        protected = self._protected_paths(protected_paths)
        write_json_atomic(self.path, {"items": [entry.to_json() for entry in remaining]})
        for raw_path in target.images:
            self._delete_orphan_image(raw_path, referenced, protected)
        return True

    def _prepend(self, item: GenerationHistoryItem, protected_paths: set[str] | None = None) -> None:
        all_items = [item, *self.items()]
        current = all_items[: self.MAX_ITEMS]
        discarded = all_items[self.MAX_ITEMS :]
        write_json_atomic(self.path, {"items": [entry.to_json() for entry in current]})
        referenced = {normalize_path(path) for entry in current for path in entry.images}
        protected = self._protected_paths(protected_paths)
        for entry in discarded:
            for raw_path in entry.images:
                self._delete_orphan_image(raw_path, referenced, protected)

    def _protected_paths(self, explicit: set[str] | None = None) -> set[str]:
        protected = {normalize_path(path) for path in (explicit or set()) if path}
        for raw in self._persistent_path_strings():
            protected.add(normalize_path(raw))
        return protected

    def _delete_orphan_image(self, raw_path: str, referenced: set[str], protected: set[str]) -> None:
        normalized = normalize_path(raw_path)
        if normalized in referenced or normalized in protected:
            return
        if not is_inside_path(raw_path, self.results_root):
            return
        try:
            Path(raw_path).unlink(missing_ok=True)
        except OSError as exc:
            self.cleanup_warnings.append(f"{raw_path}: {exc}")

    def _persistent_path_strings(self) -> list[str]:
        paths: list[str] = []
        for filename in ("library.json", "playlists.json", "settings.json"):
            data = read_json_object(data_root() / filename) or {}
            self._collect_path_strings(data, paths)
        return paths

    def _collect_path_strings(self, value: object, paths: list[str]) -> None:
        if isinstance(value, dict):
            for key, current in value.items():
                if key in {"path", "media_path", "file", "source"} and isinstance(current, str):
                    paths.append(current)
                self._collect_path_strings(current, paths)
        elif isinstance(value, list):
            for current in value:
                self._collect_path_strings(current, paths)
