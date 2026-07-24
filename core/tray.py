from __future__ import annotations

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QStyle
from core.runtime_paths import app_icon_path


class MovauraTray:
    def __init__(self, app: QApplication, engine) -> None:
        self.app = app
        self.engine = engine
        icon = QIcon(str(app_icon_path()))
        if icon.isNull():
            icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(icon if not icon.isNull() else QIcon(), app)
        self.tray.setToolTip("Movaura")
        self.tray.setContextMenu(self._build_menu())
        self.tray.activated.connect(self._activated)

    def show(self) -> None:
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        else:
            print("A bandeja do sistema não está disponível.")

    def notify_running_in_background(self) -> None:
        if self.tray.isVisible():
            self.tray.showMessage(
                "Movaura",
                "A animação continua ativa. Use o ícone da bandeja para abrir o painel.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )

    def _activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.engine.open_control_panel()

    def _build_menu(self) -> QMenu:
        menu = QMenu()
        self.status_action = QAction("Estado: em execução", menu)
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)
        menu.addSeparator()
        if self.engine.control_panel:
            open_panel = QAction("Abrir painel", menu)
            open_panel.triggered.connect(self.engine.open_control_panel)
            menu.addAction(open_panel)
            menu.addSeparator()
        self.pause_action = QAction("Pausar", menu)
        self.pause_action.triggered.connect(self.engine.pause)
        menu.addAction(self.pause_action)
        self.resume_action = QAction("Continuar", menu)
        self.resume_action.triggered.connect(self.engine.resume)
        menu.addAction(self.resume_action)
        restart_action = QAction("Reiniciar wallpapers", menu)
        restart_action.triggered.connect(self.engine.restart)
        menu.addAction(restart_action)
        next_action = QAction("Próximo item da playlist", menu)
        next_action.triggered.connect(self.engine.next_playlist_item)
        menu.addAction(next_action)
        menu.addSeparator()
        quit_action = QAction("Sair do Movaura", menu)
        quit_action.triggered.connect(self.engine.quit)
        menu.addAction(quit_action)
        return menu

    def update_state(self, paused: bool) -> None:
        self.status_action.setText("Estado: pausado" if paused else "Estado: em execução")
        self.tray.setToolTip("Movaura: pausado" if paused else "Movaura: em execução")
        self.pause_action.setEnabled(not paused)
        self.resume_action.setEnabled(paused)
