from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class RendererContext:
    renderer: str
    media_path: Path | None
    color: str
    fps: int
    low_power_mode: bool


class RendererFactory(Protocol):
    def __call__(self, context: RendererContext) -> QWidget:
        ...
