from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WallpaperSearchQuery:
    text: str
    category: str = ""
    resolution: str = ""
    orientation: str = ""
    color: str = ""
    page: int = 1
    per_page: int = 12

    @property
    def normalized_text(self) -> str:
        parts = [self.text.strip(), self.category.strip()]
        return " ".join(part for part in parts if part).strip()


@dataclass(frozen=True)
class WallpaperResult:
    provider: str
    provider_id: str
    title: str
    author: str
    author_url: str
    source_url: str
    thumbnail_url: str
    download_url: str
    width: int
    height: int
    average_color: str = ""
    media_type: str = "image"

    @property
    def resolution_label(self) -> str:
        if self.width > 0 and self.height > 0:
            return f"{self.width}x{self.height}"
        return "resolucao desconhecida"

