from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QWidget

from renderers.base import RendererContext
from renderers.color_renderer import ColorRenderer
from renderers.gif_renderer import GifRenderer
from renderers.opengl_renderer import OpenGLRenderer
from renderers.video_renderer import VideoRenderer


BUILTIN_RENDERERS = {
    "color": ColorRenderer,
    "video": VideoRenderer,
    "gif": GifRenderer,
    "opengl": OpenGLRenderer,
}


class RendererFactory:
    def __init__(self, plugin_renderers: dict | None = None) -> None:
        self.renderers = dict(BUILTIN_RENDERERS)
        if plugin_renderers:
            self.renderers.update(plugin_renderers)

    def create(self, settings) -> QWidget:
        renderer_name = settings.get_str("renderer")
        media_path = settings.get_str("media_path")
        context = RendererContext(
            renderer=renderer_name,
            media_path=Path(media_path) if media_path else None,
            color=settings.get_str("color"),
            fps=settings.get_int("fps"),
            low_power_mode=settings.get_bool("low_power_mode"),
        )

        renderer_cls = self.renderers.get(renderer_name)
        if renderer_cls is None:
            print(f"Renderer {renderer_name!r} not found, falling back to color.")
            renderer_cls = ColorRenderer

        try:
            return renderer_cls(context)
        except Exception as exc:
            print(f"Renderer {renderer_name!r} failed: {exc}. Falling back to color.")
            return ColorRenderer(context)
