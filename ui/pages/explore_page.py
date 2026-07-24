from __future__ import annotations

from pathlib import Path
from threading import Event, Thread

from PySide6.QtCore import QObject, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from downloads.download_manager import DownloadError, DownloadManager
from models.wallpaper_result import WallpaperResult, WallpaperSearchQuery
from services.wallpaper_search_service import WallpaperSearchService
from core.settings import MovauraSettings
from core.wallpaper_library import WallpaperItem, WallpaperLibrary


CATEGORIES = (
    "Anime",
    "Cyberpunk",
    "Natureza",
    "Carros",
    "Minimalista",
    "Sci-Fi",
    "Abstract",
    "Fantasy",
    "Space",
    "Cities",
    "Gaming",
    "Dark",
    "Light",
    "Tecnologia",
)

RESOLUTIONS = {
    "Qualquer": "",
    "Grande": "large",
    "Media": "medium",
    "Pequena": "small",
}

ORIENTATIONS = {
    "Qualquer": "",
    "Paisagem": "landscape",
    "Retrato": "portrait",
    "Quadrada": "square",
}

COLORS = {
    "Qualquer": "",
    "Azul": "blue",
    "Verde": "green",
    "Vermelho": "red",
    "Roxo": "purple",
    "Preto": "black",
    "Branco": "white",
    "Amarelo": "yellow",
    "Laranja": "orange",
}


class WorkerSignals(QObject):
    completed = Signal(object)
    failed = Signal(str)
    progress = Signal(int, str)


class ExplorePage(QWidget):
    wallpaper_selected = Signal(object)
    preview_requested = Signal()
    start_requested = Signal()
    library_requested = Signal(object)
    status_changed = Signal(str)

    def __init__(self, settings: MovauraSettings, library: WallpaperLibrary, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.library = library
        self.search_service = WallpaperSearchService(settings)
        self.download_manager = DownloadManager(self.search_service.cache)
        self.search_signals: WorkerSignals | None = None
        self.download_signals: WorkerSignals | None = None
        self.cancel_event = Event()
        self._build_ui()
        self._connect_signals()
        self._load_settings()
        self._refresh_actions()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel("Explorar wallpapers")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        subtitle = QLabel("Pesquise em provedores oficiais e adicione wallpapers com seguranca a sua biblioteca.")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        config_form = QFormLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Cole sua chave oficial da API do Pexels")
        self.save_key_button = QPushButton("Salvar chave")
        key_row = QHBoxLayout()
        key_row.addWidget(self.api_key_edit, 1)
        key_row.addWidget(self.save_key_button)
        config_form.addRow("API Pexels", key_row)
        root.addLayout(config_form)

        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar: cidade neon, praia, carro esportivo...")
        self.category_combo = QComboBox()
        self.category_combo.addItem("Categoria")
        self.category_combo.addItems(CATEGORIES)
        self.search_button = QPushButton("Pesquisar")
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(self.category_combo)
        search_row.addWidget(self.search_button)
        root.addLayout(search_row)

        filters = QGridLayout()
        self.resolution_combo = QComboBox()
        self.orientation_combo = QComboBox()
        self.color_combo = QComboBox()
        for label in RESOLUTIONS:
            self.resolution_combo.addItem(label, RESOLUTIONS[label])
        for label in ORIENTATIONS:
            self.orientation_combo.addItem(label, ORIENTATIONS[label])
        for label in COLORS:
            self.color_combo.addItem(label, COLORS[label])
        filters.addWidget(QLabel("Resolucao"), 0, 0)
        filters.addWidget(self.resolution_combo, 0, 1)
        filters.addWidget(QLabel("Orientacao"), 0, 2)
        filters.addWidget(self.orientation_combo, 0, 3)
        filters.addWidget(QLabel("Cor predominante"), 0, 4)
        filters.addWidget(self.color_combo, 0, 5)
        root.addLayout(filters)

        self.message_label = QLabel("Configure sua chave da API do Pexels para utilizar esta funcionalidade.")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("padding: 8px; border: 1px solid #ddd; background: #fafafa;")
        root.addWidget(self.message_label)

        self.results_list = QListWidget()
        self.results_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.results_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.results_list.setMovement(QListWidget.Movement.Static)
        self.results_list.setIconSize(QSize(190, 108))
        self.results_list.setGridSize(QSize(230, 175))
        self.results_list.setWordWrap(True)
        root.addWidget(self.results_list, 1)

        progress_row = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setEnabled(False)
        progress_row.addWidget(self.progress, 1)
        progress_row.addWidget(self.cancel_button)
        root.addLayout(progress_row)

        actions = QHBoxLayout()
        self.download_button = QPushButton("Download")
        self.apply_button = QPushButton("Aplicar Wallpaper")
        self.favorite_button = QPushButton("Favoritar")
        self.open_library_button = QPushButton("Abrir biblioteca")
        actions.addWidget(self.download_button)
        actions.addWidget(self.apply_button)
        actions.addWidget(self.favorite_button)
        actions.addStretch(1)
        actions.addWidget(self.open_library_button)
        root.addLayout(actions)

    def _connect_signals(self) -> None:
        self.save_key_button.clicked.connect(self._save_key)
        self.search_button.clicked.connect(self._search)
        self.search_edit.returnPressed.connect(self._search)
        self.cancel_button.clicked.connect(self._cancel_operation)
        self.download_button.clicked.connect(self._download_selected)
        self.apply_button.clicked.connect(self._apply_selected)
        self.favorite_button.clicked.connect(self._favorite_selected)
        self.open_library_button.clicked.connect(lambda: self.library_requested.emit(None))
        self.results_list.itemSelectionChanged.connect(self._refresh_actions)

    def _load_settings(self) -> None:
        self.api_key_edit.setText(self.settings.get_str("pexels_api_key"))
        self.search_edit.setText(self.settings.get_str("explore_last_query"))
        self._set_combo_text(self.category_combo, self.settings.get_str("explore_last_category") or "Categoria")

    def _save_key(self) -> None:
        self.settings.data["pexels_api_key"] = self.api_key_edit.text().strip()
        self.settings.save()
        self.message_label.setText("Chave da API salva com seguranca nas configuracoes locais do Movaura.")
        self.status_changed.emit("Chave da API Pexels salva.")

    def _search(self) -> None:
        if self.search_signals:
            return
        self._save_key()
        query = self._query_from_form()
        self.settings.data["explore_last_query"] = self.search_edit.text().strip()
        self.settings.data["explore_last_category"] = self.category_combo.currentText()
        self.settings.save()
        self.results_list.clear()
        self.progress.setValue(0)
        self._set_busy(True)
        self.message_label.setText("Pesquisando wallpapers...")
        self.search_signals = WorkerSignals()
        self.search_signals.completed.connect(self._search_finished)
        self.search_signals.failed.connect(self._operation_failed)

        def run() -> None:
            try:
                results = self.search_service.search(query)
                for result in results:
                    if self.cancel_event.is_set():
                        break
                    self.download_manager.download_thumbnail(result.thumbnail_url)
            except Exception as exc:
                if self.search_signals:
                    self.search_signals.failed.emit(self.search_service.friendly_error(exc))
                return
            if self.search_signals:
                self.search_signals.completed.emit(results)

        Thread(target=run, daemon=True).start()

    def _search_finished(self, payload: object) -> None:
        self.search_signals = None
        self._set_busy(False)
        results = payload if isinstance(payload, list) else []
        if not results:
            self.message_label.setText("Nenhum wallpaper encontrado com esses filtros.")
            self._refresh_actions()
            return
        for result in results:
            if isinstance(result, WallpaperResult):
                self._add_result(result)
        self.message_label.setText(f"{len(results)} resultado(s) encontrados. Selecione um item para baixar ou aplicar.")
        self.progress.setValue(100)
        self._refresh_actions()

    def _add_result(self, result: WallpaperResult) -> None:
        text = f"{result.title[:42]}\n{result.resolution_label} | {result.author}"
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, result)
        item.setToolTip(
            f"{result.title}\nAutor: {result.author}\nFonte: {result.provider}\nResolucao: {result.resolution_label}"
        )
        thumbnail = self.download_manager.cache.cached_thumbnail_for_url(result.thumbnail_url)
        if thumbnail and thumbnail.is_file():
            pixmap = QPixmap(str(thumbnail))
            if not pixmap.isNull():
                item.setIcon(
                    QIcon(
                        pixmap.scaled(
                            190,
                            108,
                            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
                )
        self.results_list.addItem(item)

    def _download_selected(self) -> None:
        result = self._selected_result()
        if not result or self.download_signals:
            return
        self.cancel_event.clear()
        self.progress.setValue(0)
        self._set_busy(True)
        self.message_label.setText("Baixando wallpaper...")
        self.download_signals = WorkerSignals()
        self.download_signals.progress.connect(self._progress_changed)
        self.download_signals.completed.connect(lambda path: self._download_finished(path, apply_now=False))
        self.download_signals.failed.connect(self._operation_failed)
        self._start_download(result)

    def _apply_selected(self) -> None:
        result = self._selected_result()
        if not result or self.download_signals:
            return
        self.cancel_event.clear()
        self.progress.setValue(0)
        self._set_busy(True)
        self.message_label.setText("Baixando e aplicando wallpaper...")
        self.download_signals = WorkerSignals()
        self.download_signals.progress.connect(self._progress_changed)
        self.download_signals.completed.connect(lambda path: self._download_finished(path, apply_now=True))
        self.download_signals.failed.connect(self._operation_failed)
        self._start_download(result)

    def _start_download(self, result: WallpaperResult) -> None:
        def run() -> None:
            try:
                path = self.download_manager.download(
                    result.download_url,
                    lambda value, message: self.download_signals.progress.emit(value, message) if self.download_signals else None,
                    self.cancel_event.is_set,
                )
            except DownloadError as exc:
                if self.download_signals:
                    self.download_signals.failed.emit(exc.user_message)
                return
            if self.download_signals:
                self.download_signals.completed.emit(path)

        Thread(target=run, daemon=True).start()

    def _download_finished(self, payload: object, apply_now: bool) -> None:
        self.download_signals = None
        self._set_busy(False)
        path = payload if isinstance(payload, Path) else None
        result = self._selected_result()
        if not path or not path.is_file() or not result:
            self.message_label.setText("Download concluido, mas o arquivo nao foi localizado.")
            return
        imported = self.library.import_files([path])
        if not imported:
            self.message_label.setText("O arquivo baixado nao e compativel com a biblioteca.")
            self._refresh_actions()
            return
        item = imported[0]
        self.library.update_details(
            item,
            [result.provider.lower(), "online", self._tag(result.title)],
            f"Online - {result.provider}",
            "leve",
        )
        if apply_now:
            self.wallpaper_selected.emit(item)
            self.start_requested.emit()
            self.message_label.setText("Wallpaper baixado e aplicado.")
            self.status_changed.emit("Wallpaper online aplicado.")
        else:
            self.message_label.setText("Wallpaper baixado para sua biblioteca.")
            self.status_changed.emit("Wallpaper online salvo na biblioteca.")
        self.progress.setValue(100)
        self._refresh_actions()

    def _favorite_selected(self) -> None:
        result = self._selected_result()
        if not result:
            return
        path = self.download_manager.cache.cached_file_for_url(result.download_url)
        existing = self._library_item_for_path(path)
        if not existing and path.is_file():
            imported = self.library.import_files([path])
            existing = imported[0] if imported else None
        if not existing:
            QMessageBox.information(self, "Favoritar", "Baixe o wallpaper antes de favoritar.")
            return
        favorite = self.library.toggle_favorite(existing)
        self.message_label.setText("Wallpaper favoritado." if favorite else "Wallpaper removido dos favoritos.")

    def _operation_failed(self, message: str) -> None:
        self.search_signals = None
        self.download_signals = None
        self._set_busy(False)
        self.progress.setValue(0)
        self.message_label.setText(message)
        self.status_changed.emit(message)

    def _progress_changed(self, value: int, message: str) -> None:
        self.progress.setValue(value)
        self.message_label.setText(message)

    def _cancel_operation(self) -> None:
        self.cancel_event.set()
        self.message_label.setText("Cancelando operacao...")

    def _query_from_form(self) -> WallpaperSearchQuery:
        category = "" if self.category_combo.currentIndex() == 0 else self.category_combo.currentText()
        return WallpaperSearchQuery(
            text=self.search_edit.text(),
            category=category,
            resolution=str(self.resolution_combo.currentData() or ""),
            orientation=str(self.orientation_combo.currentData() or ""),
            color=str(self.color_combo.currentData() or ""),
        )

    def _set_busy(self, busy: bool) -> None:
        self.search_button.setEnabled(not busy)
        self.download_button.setEnabled(not busy and self._selected_result() is not None)
        self.apply_button.setEnabled(not busy and self._selected_result() is not None)
        self.favorite_button.setEnabled(not busy and self._selected_result() is not None)
        self.cancel_button.setEnabled(busy)

    def _refresh_actions(self) -> None:
        busy = self.search_signals is not None or self.download_signals is not None
        selected = self._selected_result() is not None
        self.search_button.setEnabled(not busy)
        self.download_button.setEnabled(selected and not busy)
        self.apply_button.setEnabled(selected and not busy)
        self.favorite_button.setEnabled(selected and not busy)
        self.cancel_button.setEnabled(busy)

    def _selected_result(self) -> WallpaperResult | None:
        items = self.results_list.selectedItems()
        if not items:
            return None
        result = items[0].data(Qt.ItemDataRole.UserRole)
        return result if isinstance(result, WallpaperResult) else None

    def _library_item_for_path(self, path: Path) -> WallpaperItem | None:
        try:
            target = str(path.resolve()).lower()
        except OSError:
            target = str(path).lower()
        for item in self.library.items():
            try:
                current = str(item.path.resolve()).lower()
            except OSError:
                current = str(item.path).lower()
            if current == target:
                return item
        return None

    @staticmethod
    def _tag(value: str) -> str:
        tag = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
        return tag[:40] or "wallpaper"

    @staticmethod
    def _set_combo_text(combo: QComboBox, text: str) -> None:
        for index in range(combo.count()):
            if combo.itemText(index) == text:
                combo.setCurrentIndex(index)
                return
