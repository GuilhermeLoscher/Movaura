from PyQt6.QtCore import QTimer

from renderers.color_renderer import ColorRenderer


class PulseColorRenderer(ColorRenderer):
    def __init__(self, context) -> None:
        super().__init__(context)
        self.phase = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def start(self) -> None:
        self.timer.start(1000)

    def stop(self) -> None:
        self.timer.stop()

    def _tick(self) -> None:
        colors = ["#0078ff", "#00a36c", "#101820"]
        self.phase = (self.phase + 1) % len(colors)
        self.color.setNamedColor(colors[self.phase])
        self.update()


def register():
    return {
        "name": "Sample Pulse",
        "version": "0.1.0",
        "renderers": {
            "sample_pulse": PulseColorRenderer,
        },
    }
