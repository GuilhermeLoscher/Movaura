from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from core.wallpaper_sources.base_provider import MissingProviderKeyError, WallpaperProvider, WallpaperProviderError
from models.wallpaper_result import WallpaperResult, WallpaperSearchQuery


PEXELS_SEARCH_ENDPOINT = "https://api.pexels.com/v1/search"


class PexelsProvider(WallpaperProvider):
    provider_id = "pexels"
    display_name = "Pexels"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key.strip()

    def search(self, query: WallpaperSearchQuery) -> list[WallpaperResult]:
        if not self.api_key:
            raise MissingProviderKeyError("Configure sua chave da API do Pexels para utilizar esta funcionalidade.")
        search_text = query.normalized_text
        if not search_text:
            raise WallpaperProviderError("Digite uma busca ou escolha uma categoria antes de pesquisar.")
        params = {
            "query": search_text,
            "per_page": str(max(1, min(40, query.per_page))),
            "page": str(max(1, query.page)),
            "locale": "pt-BR",
        }
        if query.orientation:
            params["orientation"] = query.orientation
        if query.resolution:
            params["size"] = query.resolution
        if query.color:
            params["color"] = query.color
        url = f"{PEXELS_SEARCH_ENDPOINT}?{urlencode(params)}"
        request = Request(url, headers={"Authorization": self.api_key, "Accept": "application/json"})
        try:
            with urlopen(request, timeout=12) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in {401, 403}:
                raise WallpaperProviderError("A chave da API do Pexels foi recusada. Confira a chave nas configuracoes.") from exc
            if exc.code == 429:
                raise WallpaperProviderError("Limite da API do Pexels atingido. Tente novamente mais tarde.") from exc
            raise WallpaperProviderError("O Pexels recusou a pesquisa no momento.") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise WallpaperProviderError("Nao foi possivel conectar ao Pexels agora. Verifique a internet e tente novamente.") from exc
        photos = payload.get("photos", []) if isinstance(payload, dict) else []
        results = [self._map_photo(photo) for photo in photos if isinstance(photo, dict)]
        return [result for result in results if result.download_url]

    def _map_photo(self, photo: dict) -> WallpaperResult:
        src = photo.get("src", {}) if isinstance(photo.get("src"), dict) else {}
        photo_id = str(photo.get("id", ""))
        width = self._int(photo.get("width"))
        height = self._int(photo.get("height"))
        alt = str(photo.get("alt") or "").strip()
        author = str(photo.get("photographer") or "Pexels").strip()
        title = alt or f"Wallpaper Pexels {photo_id}"
        return WallpaperResult(
            provider=self.display_name,
            provider_id=photo_id,
            title=title,
            author=author,
            author_url=str(photo.get("photographer_url") or ""),
            source_url=str(photo.get("url") or ""),
            thumbnail_url=str(src.get("medium") or src.get("small") or src.get("tiny") or ""),
            download_url=str(src.get("original") or src.get("large2x") or src.get("large") or ""),
            width=width,
            height=height,
            average_color=str(photo.get("avg_color") or ""),
            media_type="image",
        )

    @staticmethod
    def _int(value: object) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

