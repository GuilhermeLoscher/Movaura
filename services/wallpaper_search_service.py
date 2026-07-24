from __future__ import annotations

from cache.wallpaper_cache import WallpaperCache
from core.settings import MovauraSettings
from core.wallpaper_sources.base_provider import WallpaperProviderError
from core.wallpaper_sources.pexels_provider import PexelsProvider
from models.wallpaper_result import WallpaperResult, WallpaperSearchQuery


class WallpaperSearchService:
    def __init__(self, settings: MovauraSettings, cache: WallpaperCache | None = None) -> None:
        self.settings = settings
        self.cache = cache or WallpaperCache()

    def search(self, query: WallpaperSearchQuery) -> list[WallpaperResult]:
        provider = self._pexels_provider()
        cached = self.cache.read_search(provider.provider_id, query)
        if cached is not None:
            return cached
        results = provider.search(query)
        self.cache.write_search(provider.provider_id, query, results)
        return results

    def friendly_error(self, exc: Exception) -> str:
        if isinstance(exc, WallpaperProviderError):
            return exc.user_message
        return "Nao foi possivel pesquisar wallpapers agora. Tente novamente em alguns minutos."

    def _pexels_provider(self) -> PexelsProvider:
        return PexelsProvider(self.settings.get_str("pexels_api_key"))

