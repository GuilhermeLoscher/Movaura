from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget

from renderers.base import RendererContext


class ColorRenderer(QWidget):
    def __init__(self, context: RendererContext) -> None:
        super().__init__()
        self.color = QColor(context.color)
        self.setAutoFillBackground(False)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.color)
