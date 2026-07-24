from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QMovie
from PySide6.QtWidgets import QLabel, QSizePolicy

from renderers.base import RendererContext


class GifRenderer(QLabel):
    def __init__(self, context: RendererContext) -> None:
        super().__init__()
        self.context = context
        self.movie: QMovie | None = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        if context.media_path and context.media_path.exists():
            self.movie = QMovie(str(context.media_path))
            self.movie.setCacheMode(QMovie.CacheMode.CacheAll)
            self.movie.frameChanged.connect(lambda _: self._scale_movie())
            self.setMovie(self.movie)
        else:
            self.setText("GIF file not found")
            print("GIF renderer needs --file pointing to a GIF file.")

    def start(self) -> None:
        if self.movie:
            self.movie.start()

    def stop(self) -> None:
        if self.movie:
            self.movie.stop()

    def resizeEvent(self, event) -> None:
        self._scale_movie()
        super().resizeEvent(event)

    def _scale_movie(self) -> None:
        if self.movie:
            self.movie.setScaledSize(self.size())
