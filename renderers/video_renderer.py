from __future__ import annotations

from PySide6.QtCore import QUrl, Qt
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget

from renderers.base import RendererContext


class VideoRenderer(QVideoWidget):
    def __init__(self, context: RendererContext) -> None:
        super().__init__()
        self.context = context
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setMuted(True)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self)
        self.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)

        if context.media_path and context.media_path.exists():
            self.player.setSource(QUrl.fromLocalFile(str(context.media_path)))
        else:
            print("Video renderer needs --file pointing to an MP4/WebM file.")

        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

    def start(self) -> None:
        if self.player.source().isValid():
            self.player.play()

    def stop(self) -> None:
        self.player.stop()

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setPosition(0)
            self.player.play()
