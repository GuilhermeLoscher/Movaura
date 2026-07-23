from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationStyle:
    id: str
    name: str
    suffix: str
    palette: tuple[str, str, str]


STYLES = (
    GenerationStyle(
        id="cinematic",
        name="Cinematico",
        suffix="composicao cinematica, luz suave, profundidade, wallpaper premium",
        palette=("#101827", "#2dd4bf", "#8b5cf6"),
    ),
    GenerationStyle(
        id="anime",
        name="Anime premium",
        suffix="arte anime limpa, detalhes finos, brilho controlado, fundo imersivo",
        palette=("#111827", "#60a5fa", "#f472b6"),
    ),
    GenerationStyle(
        id="games",
        name="Jogos e neon",
        suffix="visual de jogo moderno, neon, contraste alto, energia, sem texto",
        palette=("#050505", "#22c55e", "#06b6d4"),
    ),
    GenerationStyle(
        id="nature",
        name="Natureza viva",
        suffix="natureza detalhada, atmosfera calma, luz natural, profundidade suave",
        palette=("#10231a", "#84cc16", "#38bdf8"),
    ),
    GenerationStyle(
        id="abstract",
        name="Abstrato fluido",
        suffix="formas abstratas fluidas, gradientes limpos, movimento visual elegante",
        palette=("#171717", "#f97316", "#14b8a6"),
    ),
    GenerationStyle(
        id="minimal",
        name="Minimalista leve",
        suffix="minimalista, baixa distracao, elegante, area livre para icones",
        palette=("#f8fafc", "#0f172a", "#64748b"),
    ),
)


RESOLUTIONS = {
    "HD 1366x768": (1366, 768),
    "Full HD 1920x1080": (1920, 1080),
    "2K 2560x1440": (2560, 1440),
    "4K 3840x2160": (3840, 2160),
    "Ultrawide 3440x1440": (3440, 1440),
}


QUALITY_LABELS = {
    "fast": "Rapida",
    "recommended": "Recomendada",
    "max": "Maxima qualidade",
}


def style_by_id(style_id: str) -> GenerationStyle:
    for style in STYLES:
        if style.id == style_id:
            return style
    return STYLES[0]


def enhance_prompt(prompt: str, style_id: str, negative_prompt: str = "") -> str:
    clean = " ".join(prompt.strip().split())
    style = style_by_id(style_id)
    if not clean:
        clean = "wallpaper original para area de trabalho"
    parts = [
        clean,
        style.suffix,
        "alta nitidez",
        "sem marcas d'agua",
        "sem logotipos",
        "composicao adequada para icones do desktop",
    ]
    if negative_prompt.strip():
        parts.append(f"evitar: {negative_prompt.strip()}")
    return ", ".join(parts)
