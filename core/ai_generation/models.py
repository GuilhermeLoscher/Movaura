from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class GenerationState(str, Enum):
    IDLE = "idle"
    QUEUED = "queued"
    ENHANCING_PROMPT = "enhancing_prompt"
    GENERATING = "generating"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GenerationErrorCode(str, Enum):
    AUTH = "auth"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    EMPTY_RESULT = "empty_result"
    INVALID_IMAGE = "invalid_image"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProviderCapabilities:
    name: str
    display_name: str
    mock: bool
    supports_image: bool = True
    supports_video: bool = False
    supports_variations: bool = True
    supports_seed: bool = True
    max_images: int = 4


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    enhanced_prompt: str
    negative_prompt: str
    style_id: str
    style_name: str
    resolution: tuple[int, int]
    quantity: int
    quality: str
    seed: int | None = None
    provider_id: str = "mock"
    simulate_error: str = ""
    source_image: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def final_prompt(self) -> str:
        return self.enhanced_prompt or self.prompt


@dataclass(frozen=True)
class GenerationImage:
    path: Path
    width: int
    height: int
    seed: int
    prompt: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationError(Exception):
    code: GenerationErrorCode
    user_message: str
    technical_message: str = ""

    def __str__(self) -> str:
        return self.user_message


@dataclass(frozen=True)
class GenerationResult:
    provider_id: str
    request: GenerationRequest
    images: list[GenerationImage]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationHistoryItem:
    id: str
    created_at: str
    provider_id: str
    prompt: str
    enhanced_prompt: str
    style_id: str
    style_name: str
    resolution: str
    quality: str
    images: list[str]
    status: str
    message: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "provider_id": self.provider_id,
            "prompt": self.prompt,
            "enhanced_prompt": self.enhanced_prompt,
            "style_id": self.style_id,
            "style_name": self.style_name,
            "resolution": self.resolution,
            "quality": self.quality,
            "images": list(self.images),
            "status": self.status,
            "message": self.message,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "GenerationHistoryItem":
        images = data.get("images", [])
        if not isinstance(images, list):
            images = []
        return cls(
            id=str(data.get("id", "")),
            created_at=str(data.get("created_at", "")),
            provider_id=str(data.get("provider_id", "mock")),
            prompt=str(data.get("prompt", "")),
            enhanced_prompt=str(data.get("enhanced_prompt", "")),
            style_id=str(data.get("style_id", "cinematic")),
            style_name=str(data.get("style_name", "Cinematico")),
            resolution=str(data.get("resolution", "")),
            quality=str(data.get("quality", "recommended")),
            images=[str(item) for item in images],
            status=str(data.get("status", "completed")),
            message=str(data.get("message", "")),
        )
