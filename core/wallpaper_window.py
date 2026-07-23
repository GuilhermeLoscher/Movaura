from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget


class WallpaperWindow(QWidget):
    def __init__(self, renderer_widget: QWidget, title: str) -> None:
        super().__init__()
        self.renderer_widget = renderer_widget
        self.keep_bottom_geometry: tuple[int, int, int, int] | None = None
        self.keep_bottom_timer = QTimer(self)
        self.keep_bottom_timer.timeout.connect(self._keep_bottom)
        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(renderer_widget)

    def enable_input_passthrough(self) -> None:
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus, True)
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, True)

    def start(self) -> None:
        start = getattr(self.renderer_widget, "start", None)
        if callable(start):
            start()

    def stop(self) -> None:
        self.keep_bottom_timer.stop()
        stop = getattr(self.renderer_widget, "stop", None)
        if callable(stop):
            stop()

    def enable_keep_bottom(self, geometry: tuple[int, int, int, int], interval_ms: int = 1000) -> None:
        self.keep_bottom_geometry = geometry
        self.keep_bottom_timer.start(interval_ms)

    def _keep_bottom(self) -> None:
        if not self.keep_bottom_geometry:
            return

        from core.window_styles import keep_desktop_overlay_bottom

        keep_desktop_overlay_bottom(int(self.winId()), *self.keep_bottom_geometry)
