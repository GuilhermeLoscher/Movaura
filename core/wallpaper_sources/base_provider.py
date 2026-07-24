from __future__ import annotations

from abc import ABC, abstractmethod

from models.wallpaper_result import WallpaperResult, WallpaperSearchQuery


class WallpaperProviderError(RuntimeError):
    def __init__(self, user_message: str, technical_message: str = "") -> None:
        super().__init__(technical_message or user_message)
        self.user_message = user_message
        self.technical_message = technical_message or user_message


class MissingProviderKeyError(WallpaperProviderError):
    pass


class WallpaperProvider(ABC):
    provider_id: str
    display_name: str

    @abstractmethod
    def search(self, query: WallpaperSearchQuery) -> list[WallpaperResult]:
        raise NotImplementedError

