from __future__ import annotations

import math

from PyQt6.QtCore import QElapsedTimer, QTimer, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

from renderers.base import RendererContext


class OpenGLRenderer(QOpenGLWidget):
    def __init__(self, context: RendererContext) -> None:
        super().__init__()
        self.context = context
        self.clock = QElapsedTimer()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.interval_ms = max(7, int(1000 / max(1, context.fps)))
        self.setUpdateBehavior(QOpenGLWidget.UpdateBehavior.PartialUpdate)

    def start(self) -> None:
        self.clock.start()
        self.timer.start(self.interval_ms)

    def stop(self) -> None:
        self.timer.stop()

    def paintGL(self) -> None:
        elapsed = self.clock.elapsed() / 1000 if self.clock.isValid() else 0
        pulse = (math.sin(elapsed * 0.8) + 1) / 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(0, 120, 255))
        gradient.setColorAt(0.55, QColor(10, int(80 + 80 * pulse), 190))
        gradient.setColorAt(1.0, QColor(0, 22, 48))
        painter.fillRect(self.rect(), gradient)

        radius = min(self.width(), self.height()) * (0.16 + 0.05 * pulse)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 32))
        painter.drawEllipse(
            int(self.width() * (0.5 + 0.2 * math.sin(elapsed * 0.35)) - radius),
            int(self.height() * 0.5 - radius),
            int(radius * 2),
            int(radius * 2),
        )
        painter.end()
