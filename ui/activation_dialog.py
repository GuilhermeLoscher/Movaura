from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from core.license_manager import LicenseManager


class ActivationDialog(QDialog):
    def __init__(self, license_manager: LicenseManager) -> None:
        super().__init__()
        self.license_manager = license_manager
        self.setWindowTitle("Ativar Movaura Beta")
        self.setMinimumWidth(430)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("MOVAURA-BETA-XXXX-XXXX-XXXX")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("seu@email.com")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Opcional")

        intro = QLabel(
            "Esta versao beta precisa de uma chave unica. "
            "Cada chave fica vinculada ao primeiro computador ativado."
        )
        intro.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Chave beta", self.key_input)
        form.addRow("E-mail", self.email_input)
        form.addRow("Nome", self.name_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Ativar")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Sair")
        buttons.accepted.connect(self._activate)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _activate(self) -> None:
        result = self.license_manager.activate(
            self.key_input.text(),
            self.email_input.text(),
            self.name_input.text(),
        )
        if result.success:
            QMessageBox.information(self, "Movaura ativado", result.message)
            self.accept()
            return
        QMessageBox.warning(self, "Nao foi possivel ativar", result.message)
