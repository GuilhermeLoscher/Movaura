"""Offline AI generation architecture for Movaura."""

from core.ai_generation.models import (
    GenerationError,
    GenerationHistoryItem,
    GenerationImage,
    GenerationRequest,
    GenerationResult,
    GenerationState,
    ProviderCapabilities,
)
from core.ai_generation.providers import MockImageGenerationProvider
from core.ai_generation.storage import GenerationHistoryStore, GenerationStorage

__all__ = [
    "GenerationError",
    "GenerationHistoryItem",
    "GenerationImage",
    "GenerationRequest",
    "GenerationResult",
    "GenerationState",
    "ProviderCapabilities",
    "MockImageGenerationProvider",
    "GenerationHistoryStore",
    "GenerationStorage",
]
