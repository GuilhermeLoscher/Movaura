from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


LAYER_TYPES = ("background", "effect", "audio")
BLEND_MODES = ("normal", "screen", "multiply", "overlay")
EFFECTS = ("pulse", "parallax", "audio", "particles", "rain", "fog", "glow", "vignette")


@dataclass
class SceneLayer:
    name: str
    kind: str = "effect"
    effect: str = "pulse"
    enabled: bool = True
    opacity: int = 100
    x: int = 0
    y: int = 0
    scale: int = 100
    blend: str = "normal"
    media_path: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def default_layers(media_path: str = "", renderer: str = "parallax") -> list[dict[str, object]]:
    effect = renderer if renderer in EFFECTS else "pulse"
    return [
        SceneLayer("Fundo", kind="background", effect="media", media_path=media_path).to_dict(),
        SceneLayer("Efeito principal", kind="effect", effect=effect, opacity=70).to_dict(),
    ]


def normalize_layers(value: Any, media_path: str = "", renderer: str = "parallax") -> list[dict[str, object]]:
    if not isinstance(value, list) or not value:
        return default_layers(media_path, renderer)
    layers: list[dict[str, object]] = []
    for index, raw in enumerate(value[:16]):
        if not isinstance(raw, dict):
            continue
        kind = str(raw.get("kind", "effect"))
        effect = str(raw.get("effect", "pulse"))
        blend = str(raw.get("blend", "normal"))
        layer = SceneLayer(
            name=str(raw.get("name", f"Camada {index + 1}"))[:80],
            kind=kind if kind in LAYER_TYPES else "effect",
            effect=effect if effect in (*EFFECTS, "media") else "pulse",
            enabled=bool(raw.get("enabled", True)),
            opacity=_bounded_int(raw.get("opacity"), 100, 0, 100),
            x=_bounded_int(raw.get("x"), 0, -100, 100),
            y=_bounded_int(raw.get("y"), 0, -100, 100),
            scale=_bounded_int(raw.get("scale"), 100, 10, 300),
            blend=blend if blend in BLEND_MODES else "normal",
            media_path=str(raw.get("media_path", "")),
        )
        layers.append(layer.to_dict())
    return layers or default_layers(media_path, renderer)


def primary_effect(layers: list[dict[str, object]], fallback: str = "parallax") -> str:
    for layer in reversed(layers):
        if layer.get("enabled") and layer.get("kind") in {"effect", "audio"}:
            effect = str(layer.get("effect", fallback))
            if effect in EFFECTS:
                return effect
    return fallback


def primary_background(layers: list[dict[str, object]], fallback: str = "") -> str:
    for layer in layers:
        if layer.get("enabled") and layer.get("kind") == "background":
            return str(layer.get("media_path", fallback))
    return fallback


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(int(value), maximum))
    except (TypeError, ValueError):
        return default
