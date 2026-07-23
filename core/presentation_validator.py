from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


COLOR_RENDERERS = {"audio", "color", "opengl", "parallax", "particles", "rain", "fog", "glow", "vignette", "sample_pulse"}
MEDIA_EXTENSIONS = {
    "image": {".bmp", ".jpeg", ".jpg", ".png", ".webp"},
    "gif": {".gif"},
    "video": {".mp4", ".webm"},
}
MODE_RENDERERS = {
    "desktop-static": {"color", "image"},
    "animated-preview": {"audio", "color", "gif", "image", "opengl", "parallax", "particles", "rain", "fog", "glow", "vignette", "sample_pulse", "video"},
    "animated-desktop": {"audio", "color", "gif", "image", "opengl", "parallax", "particles", "rain", "fog", "glow", "vignette", "sample_pulse", "video"},
    "fullscreen-test": {"audio", "color", "gif", "image", "opengl", "parallax", "particles", "rain", "fog", "glow", "vignette", "sample_pulse", "video"},
}
HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True)
class PresentationValidation:
    success: bool
    message: str = ""


class PresentationValidator:
    def validate(self, settings: dict[str, Any]) -> PresentationValidation:
        mode = str(settings.get("experience_mode", "desktop-static"))
        renderer = str(settings.get("renderer", "color"))

        compatible_renderers = MODE_RENDERERS.get(mode)
        if not compatible_renderers:
            return PresentationValidation(False, "Selecione um modo de apresentação válido.")
        if renderer not in compatible_renderers:
            return PresentationValidation(
                False,
                "O renderizador selecionado não está disponível neste modo.",
            )

        if renderer in COLOR_RENDERERS:
            color = str(settings.get("color", "")).strip()
            if not HEX_COLOR_PATTERN.fullmatch(color):
                return PresentationValidation(
                    False,
                    "Informe uma cor hexadecimal no formato #0078ff.",
                )

        if renderer in MEDIA_EXTENSIONS:
            media_path = str(settings.get("media_path", "")).strip()
            if not media_path:
                return PresentationValidation(False, "Escolha um arquivo de mídia.")
            path = Path(media_path).expanduser()
            if not path.is_file():
                return PresentationValidation(False, "O arquivo de mídia não foi encontrado.")
            if path.suffix.lower() not in MEDIA_EXTENSIONS[renderer]:
                allowed = ", ".join(sorted(MEDIA_EXTENSIONS[renderer]))
                return PresentationValidation(
                    False,
                    f"Formato incompatível. Use um arquivo: {allowed}.",
                )

        if renderer in {"audio", "parallax", "particles", "rain", "fog", "glow", "vignette"}:
            media_path = str(settings.get("media_path", "")).strip()
            if media_path:
                path = Path(media_path).expanduser()
                allowed = set().union(*MEDIA_EXTENSIONS.values())
                if not path.is_file():
                    return PresentationValidation(False, "O arquivo usado como fundo não foi encontrado.")
                if path.suffix.lower() not in allowed:
                    return PresentationValidation(False, "Use uma imagem, GIF ou vídeo compatível como fundo.")

        if mode != "desktop-static":
            try:
                fps = int(settings.get("fps", 30))
            except (TypeError, ValueError):
                return PresentationValidation(False, "Informe um valor de FPS entre 1 e 60.")
            if not 1 <= fps <= 60:
                return PresentationValidation(False, "Informe um valor de FPS entre 1 e 60.")
            try:
                intensity = int(settings.get("effect_intensity", 70))
                speed = int(settings.get("effect_speed", 100))
            except (TypeError, ValueError):
                return PresentationValidation(False, "Os ajustes do efeito são inválidos.")
            if not 0 <= intensity <= 100 or not 10 <= speed <= 200:
                return PresentationValidation(False, "Use intensidade de 0 a 100 e velocidade de 10 a 200.")

        return PresentationValidation(True)
