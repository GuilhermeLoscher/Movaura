from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class AIFuturePage(QWidget):
    wallpaper_selected = Signal(object)
    preview_requested = Signal()
    start_requested = Signal()
    stop_requested = Signal()
    library_requested = Signal(object)
    status_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)
        root.addStretch(1)
        title = QLabel("Geracao por Inteligencia Artificial")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        message = QLabel(
            "Este recurso esta em desenvolvimento.\n\n"
            "Em breve voce podera criar wallpapers exclusivos utilizando Inteligencia Artificial diretamente no Movaura.\n\n"
            "Planejado para futuras versoes."
        )
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)
        message.setStyleSheet("font-size: 14px; color: #444;")
        notify = QPushButton("Avisar quando disponivel")
        notify.setMinimumHeight(36)
        notify.clicked.connect(lambda: self.status_changed.emit("Recurso de IA registrado como interesse futuro."))
        root.addWidget(title)
        root.addWidget(message)
        root.addWidget(notify, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addStretch(2)

    def shutdown(self) -> bool:
        return True

