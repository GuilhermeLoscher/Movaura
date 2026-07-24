from __future__ import annotations

import logging
from pathlib import Path
from threading import Thread

from PySide6.QtCore import QObject, QUrl, QSize, Qt, Signal
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFileIconProvider,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QInputDialog,
    QVBoxLayout,
)

from core.media_analyzer import analyze_media
from core.wallpaper_library import LIBRARY_CATEGORIES, WallpaperItem, WallpaperLibrary
from core.thumbnail_cache import ThumbnailCache, image_dimensions

LOGGER = logging.getLogger(__name__)


FILTERS = {
    "Todos": "",
    "Favoritos": "favorite",
    "Recentes": "recent",
    "Imagens": "image",
    "GIFs": "gif",
    "Videos": "video",
    **{category: f"category:{category}" for category in LIBRARY_CATEGORIES},
    "Importados": "personal",
    "Leves": "leve",
    "Medios": "medio",
    "Pesados": "pesado",
    "4K": "4k",
}
SORTS = (
    "Nome A-Z",
    "Nome Z-A",
    "Mais recentes",
    "Mais antigos",
    "Maior tamanho",
    "Menor tamanho",
    "Usados recentemente",
    "Favoritos primeiro",
)


class ImportSignals(QObject):
    completed = Signal(object, str)
    failed = Signal(str)


class LibraryDialog(QDialog):
    selected = Signal(object)
    preview_requested = Signal(object)

    def __init__(self, library: WallpaperLibrary, parent=None, initial_path: Path | None = None) -> None:
        super().__init__(parent)
        self.library = library
        self.initial_path = initial_path
        self.thumbnails = ThumbnailCache(self)
        self.thumbnails.ready.connect(lambda _: self.refresh())
        self.import_signals = ImportSignals(self)
        self.import_signals.completed.connect(self._import_finished)
        self.import_signals.failed.connect(self._import_failed)
        self.importing = False
        self.setWindowTitle("Biblioteca de wallpapers")
        self.resize(940, 650)
        self.setAcceptDrops(True)
        self._build_ui()
        self._load_ui_state()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar wallpaper")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(FILTERS)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(SORTS)
        self.import_button = QPushButton("Importar arquivos")
        self.import_folder_button = QPushButton("Importar pasta")
        self.clear_search_button = QPushButton("Limpar")
        toolbar.addWidget(self.search_edit, 1)
        toolbar.addWidget(self.clear_search_button)
        toolbar.addWidget(self.filter_combo)
        toolbar.addWidget(self.sort_combo)
        toolbar.addWidget(self.import_button)
        toolbar.addWidget(self.import_folder_button)
        root.addLayout(toolbar)

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setIconSize(QSize(190, 108))
        self.list_widget.setGridSize(QSize(220, 155))
        self.list_widget.setWordWrap(True)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.setStyleSheet("QListWidget::item { padding: 6px; } QListWidget::item:selected { background: #dbeafe; }")
        root.addWidget(self.list_widget, 1)
        self.empty_label = QLabel("Nenhum wallpaper encontrado. Importe arquivos ou ajuste a busca.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("padding: 10px; color: #666;")
        self.empty_label.hide()
        root.addWidget(self.empty_label)
        self.status_label = QLabel("Arraste arquivos aqui ou use Importar arquivos.")
        self.status_label.setStyleSheet("color: #555;")
        root.addWidget(self.status_label)

        footer = QHBoxLayout()
        self.summary_label = QLabel()
        self.favorite_button = QPushButton("Favoritar")
        self.details_button = QPushButton("Editar tags")
        self.locate_button = QPushButton("Localizar ausentes")
        self.remove_button = QPushButton("Remover importado")
        self.preview_button = QPushButton("Pré-visualizar")
        self.choose_button = QPushButton("Usar wallpaper")
        footer.addWidget(self.summary_label, 1)
        footer.addWidget(self.favorite_button)
        footer.addWidget(self.details_button)
        footer.addWidget(self.locate_button)
        footer.addWidget(self.remove_button)
        footer.addWidget(self.preview_button)
        footer.addWidget(self.choose_button)
        root.addLayout(footer)

        self.search_edit.textChanged.connect(self.refresh)
        self.filter_combo.currentTextChanged.connect(self.refresh)
        self.sort_combo.currentTextChanged.connect(self.refresh)
        self.clear_search_button.clicked.connect(self.search_edit.clear)
        self.import_button.clicked.connect(self._import_files)
        self.import_folder_button.clicked.connect(self._import_folder)
        self.favorite_button.clicked.connect(self._toggle_favorite)
        self.details_button.clicked.connect(self._edit_details)
        self.locate_button.clicked.connect(self._locate_missing)
        self.remove_button.clicked.connect(self._remove_selected)
        self.preview_button.clicked.connect(self._preview_selected)
        self.choose_button.clicked.connect(self._choose_selected)
        self.list_widget.itemDoubleClicked.connect(lambda _: self._choose_selected())
        self.list_widget.itemSelectionChanged.connect(self._selection_changed)
        self.list_widget.customContextMenuRequested.connect(self._open_context_menu)

    def _load_ui_state(self) -> None:
        state = self.library.ui_state()
        self.search_edit.setText(str(state.get("search", "")))
        self._set_combo_text(self.filter_combo, str(state.get("filter", "Todos")))
        self._set_combo_text(self.sort_combo, str(state.get("sort", "Nome A-Z")))

    def refresh(self) -> None:
        search = self.search_edit.text().strip().lower()
        current_filter = FILTERS[self.filter_combo.currentText()]
        self.library.update_ui_state(
            search=self.search_edit.text().strip(),
            filter=self.filter_combo.currentText(),
            sort=self.sort_combo.currentText(),
        )
        self.list_widget.clear()
        wallpapers = self._sorted_items(self.library.items())
        for wallpaper in wallpapers:
            searchable = " ".join(
                (
                    wallpaper.name,
                    wallpaper.file_name,
                    wallpaper.extension,
                    wallpaper.kind,
                    wallpaper.category,
                    wallpaper.collection,
                    *wallpaper.tags,
                )
            ).lower()
            if search and search not in searchable:
                continue
            if current_filter == "favorite" and not wallpaper.favorite:
                continue
            if current_filter == "personal" and wallpaper.included:
                continue
            if current_filter == "recent" and not wallpaper.recent:
                continue
            if current_filter in {"leve", "medio", "pesado"} and wallpaper.resource_class != current_filter:
                continue
            if current_filter == "4k" and "4k" not in wallpaper.tags:
                continue
            if current_filter.startswith("category:") and wallpaper.category != current_filter.split(":", 1)[1]:
                continue
            if current_filter and current_filter not in {"favorite", "personal", "recent", "leve", "medio", "pesado", "4k"}:
                if current_filter.startswith("category:"):
                    pass
                elif wallpaper.kind != current_filter:
                    continue
            item = QListWidgetItem(self._label(wallpaper))
            item.setData(Qt.ItemDataRole.UserRole, wallpaper)
            item.setToolTip(self._details_text(wallpaper))
            item.setIcon(self._icon(wallpaper))
            self.list_widget.addItem(item)
            if self.initial_path and wallpaper.path.resolve() == self.initial_path.resolve():
                self.list_widget.setCurrentItem(item)
                self.list_widget.scrollToItem(item)
        stats = self.library.stats()
        self.summary_label.setText(
            f"{stats['total']} arquivos | {stats['favorites']} favoritos | "
            f"{stats['personal']} importados"
        )
        self.empty_label.setVisible(self.list_widget.count() == 0)
        self._selection_changed()

    def _sorted_items(self, wallpapers: list[WallpaperItem]) -> list[WallpaperItem]:
        selected = self.sort_combo.currentText()
        if selected == "Nome Z-A":
            return sorted(wallpapers, key=lambda item: item.name.lower(), reverse=True)
        if selected == "Mais recentes":
            return sorted(wallpapers, key=lambda item: (item.imported_at, item.modified_at, item.name.lower()), reverse=True)
        if selected == "Mais antigos":
            return sorted(wallpapers, key=lambda item: (item.imported_at, item.modified_at, item.name.lower()))
        if selected == "Maior tamanho":
            return sorted(wallpapers, key=lambda item: (item.size_bytes, item.name.lower()), reverse=True)
        if selected == "Menor tamanho":
            return sorted(wallpapers, key=lambda item: (item.size_bytes, item.name.lower()))
        if selected == "Usados recentemente":
            return sorted(wallpapers, key=lambda item: (item.last_used_at, -self.library.recent_rank(item)), reverse=True)
        if selected == "Favoritos primeiro":
            return sorted(wallpapers, key=lambda item: (not item.favorite, item.name.lower()))
        return sorted(wallpapers, key=lambda item: item.name.lower())

    def _import_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Importar pasta de wallpapers", str(Path.home()))
        if not folder:
            return
        self._start_import([Path(folder)], "Importando pasta...")

    def _import_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Importar wallpapers",
            str(Path.home()),
            "Wallpapers (*.mp4 *.webm *.gif *.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not paths:
            return
        self._start_import([Path(path) for path in paths], "Importando arquivos...")

    def _start_import(self, paths: list[Path], message: str) -> None:
        if self.importing:
            self.status_label.setText("Uma importacao ja esta em andamento.")
            return
        self.importing = True
        self._set_import_busy(True)
        self.status_label.setText(message)

        def run() -> None:
            try:
                imported = self.import_paths(paths)
            except Exception:
                LOGGER.exception("Falha inesperada ao importar wallpapers.")
                self.import_signals.failed.emit("Nao foi possivel importar os wallpapers selecionados.")
                return
            self.import_signals.completed.emit(imported, self._import_message(imported))

        Thread(target=run, daemon=True).start()

    def _import_finished(self, imported: object, message: str) -> None:
        self.importing = False
        self._set_import_busy(False)
        self.refresh()
        self.status_label.setText(message)
        if imported:
            QMessageBox.information(self, "Importacao concluida", message)

    def _import_failed(self, message: str) -> None:
        self.importing = False
        self._set_import_busy(False)
        self.status_label.setText(message)
        QMessageBox.warning(self, "Importacao", message)

    def _set_import_busy(self, busy: bool) -> None:
        self.import_button.setEnabled(not busy)
        self.import_folder_button.setEnabled(not busy)

    def import_paths(self, paths: list[Path]) -> list[WallpaperItem]:
        imported: list[WallpaperItem] = []
        seen: set[str] = set()
        for path in paths:
            try:
                key = str(path.resolve()).lower()
                if key in seen:
                    continue
                seen.add(key)
                if path.is_dir():
                    imported.extend(self.library.import_folder(path))
                elif path.is_file() and self.library.kind_for_path(path):
                    imported.extend(self.library.import_files([path]))
            except OSError:
                continue
        return imported

    def _toggle_favorite(self) -> None:
        wallpaper = self._selected()
        if wallpaper:
            self.library.toggle_favorite(wallpaper)
            self.refresh()

    def _edit_details(self) -> None:
        wallpaper = self._selected()
        if not wallpaper:
            return
        tags, ok = QInputDialog.getText(self, "Tags", "Tags separadas por virgula", text=", ".join(wallpaper.tags))
        if not ok:
            return
        collection, ok = QInputDialog.getText(self, "Colecao", "Nome da colecao", text=wallpaper.collection)
        if ok:
            self.library.update_details(wallpaper, tags.split(","), collection)
            self.refresh()

    def _locate_missing(self) -> None:
        missing = self.library.missing_files()
        if not missing:
            QMessageBox.information(self, "Arquivos ausentes", "Nenhum arquivo ausente foi encontrado.")
            return
        replacement, _ = QFileDialog.getOpenFileName(self, f"Localizar substituto para {Path(missing[0]).name}", str(Path.home()))
        if replacement and self.library.locate_missing(missing[0], Path(replacement)):
            self.refresh()

    def _remove_selected(self) -> None:
        wallpaper = self._selected()
        if not wallpaper or wallpaper.included:
            return
        answer = QMessageBox.question(
            self,
            "Remover wallpaper",
            f"Remover '{wallpaper.name}' da biblioteca pessoal?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.library.remove_personal(wallpaper)
            self.refresh()

    def _rename_selected(self) -> None:
        wallpaper = self._selected()
        if not wallpaper or wallpaper.included:
            return
        name, ok = QInputDialog.getText(self, "Renomear wallpaper", "Novo nome", text=wallpaper.path.stem)
        if not ok:
            return
        renamed = self.library.rename_personal(wallpaper, name)
        if not renamed:
            QMessageBox.warning(self, "Renomear wallpaper", "Nao foi possivel renomear este wallpaper.")
            return
        self.initial_path = renamed.path
        self.refresh()

    def _open_selected_folder(self) -> None:
        wallpaper = self._selected()
        if wallpaper:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(wallpaper.path.parent)))

    def _choose_selected(self) -> None:
        wallpaper = self._selected()
        if wallpaper:
            self.library.mark_recent(wallpaper)
            self.selected.emit(wallpaper)
            self.accept()

    def _preview_selected(self) -> None:
        wallpaper = self._selected()
        if wallpaper:
            self.preview_requested.emit(wallpaper)

    def _selection_changed(self) -> None:
        wallpaper = self._selected()
        self.choose_button.setEnabled(bool(wallpaper))
        self.favorite_button.setEnabled(bool(wallpaper))
        self.details_button.setEnabled(bool(wallpaper))
        self.locate_button.setEnabled(bool(self.library.missing_files()))
        self.remove_button.setEnabled(bool(wallpaper and not wallpaper.included))
        self.preview_button.setEnabled(bool(wallpaper))
        if wallpaper:
            self.favorite_button.setText("Desfavoritar" if wallpaper.favorite else "Favoritar")

    def _open_context_menu(self, position) -> None:
        item = self.list_widget.itemAt(position)
        if item:
            self.list_widget.setCurrentItem(item)
        wallpaper = self._selected()
        if not wallpaper:
            return
        menu = QMenu(self)
        apply_action = QAction("Aplicar", self)
        favorite_action = QAction("Remover favorito" if wallpaper.favorite else "Favoritar", self)
        folder_action = QAction("Abrir pasta", self)
        rename_action = QAction("Renomear", self)
        delete_action = QAction("Excluir", self)
        preview_action = QAction("Pre-visualizar", self)
        apply_action.triggered.connect(self._choose_selected)
        preview_action.triggered.connect(self._preview_selected)
        favorite_action.triggered.connect(self._toggle_favorite)
        folder_action.triggered.connect(self._open_selected_folder)
        rename_action.triggered.connect(self._rename_selected)
        delete_action.triggered.connect(self._remove_selected)
        menu.addAction(apply_action)
        menu.addAction(preview_action)
        menu.addSeparator()
        menu.addAction(favorite_action)
        menu.addAction(folder_action)
        menu.addSeparator()
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        rename_action.setEnabled(not wallpaper.included)
        delete_action.setEnabled(not wallpaper.included)
        menu.exec(self.list_widget.mapToGlobal(position))

    def _selected(self) -> WallpaperItem | None:
        items = self.list_widget.selectedItems()
        return items[0].data(Qt.ItemDataRole.UserRole) if items else None

    def dragEnterEvent(self, event) -> None:
        if self._supported_drop_paths(event):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        paths = self._supported_drop_paths(event)
        if paths:
            self._start_import(paths, f"Importando {len(paths)} item(ns) arrastado(s)...")
            event.acceptProposedAction()
            return
        imported = self.import_paths(paths)
        self.refresh()
        if imported:
            QMessageBox.information(
                self,
                "Importação concluída",
                f"{len(imported)} arquivo(s) adicionado(s) à sua biblioteca.",
            )
        event.acceptProposedAction()

    def _supported_drop_paths(self, event) -> list[Path]:
        if not event.mimeData().hasUrls():
            return []
        paths: list[Path] = []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.is_dir() or (path.is_file() and self.library.kind_for_path(path)):
                paths.append(path)
        return paths

    @staticmethod
    def _label(wallpaper: WallpaperItem) -> str:
        favorite = " ★" if wallpaper.favorite else ""
        source = "incluido" if wallpaper.included else "importado"
        collection = f" | {wallpaper.collection}" if wallpaper.collection else ""
        resource = {"leve": "Leve", "medio": "Medio", "pesado": "Pesado"}.get(wallpaper.resource_class, "Leve")
        return f"{wallpaper.name}{favorite}\n{wallpaper.category} | {source}{collection} | {resource}"

    def _icon(self, wallpaper: WallpaperItem) -> QIcon:
        if wallpaper.kind in {"image", "gif"}:
            pixmap = QPixmap(str(wallpaper.path))
            if not pixmap.isNull():
                return QIcon(
                    pixmap.scaled(
                        190,
                        108,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        if wallpaper.kind == "video":
            static_dir = wallpaper.path.parent.parent / "static"
            for suffix in (".jpg", ".jpeg", ".png", ".webp"):
                thumbnail = static_dir / f"{wallpaper.path.stem}{suffix}"
                pixmap = QPixmap(str(thumbnail))
                if not pixmap.isNull():
                    return QIcon(
                        pixmap.scaled(
                            190,
                            108,
                            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
            cached = self.thumbnails.cached_path(wallpaper.path)
            pixmap = QPixmap(str(cached))
            if not pixmap.isNull():
                return QIcon(pixmap.scaled(190, 108))
            self.thumbnails.request_video(wallpaper.path)
        return QFileIconProvider().icon(QFileIconProvider.IconType.File)

    def _details_text(self, wallpaper: WallpaperItem) -> str:
        size_mb = wallpaper.path.stat().st_size / (1024 * 1024)
        dimensions = image_dimensions(wallpaper.path)
        metadata = self.thumbnails.metadata(wallpaper.path)
        if not dimensions and metadata.get("width") and metadata.get("height"):
            dimensions = int(metadata["width"]), int(metadata["height"])
        resolution = f"{dimensions[0]}x{dimensions[1]}" if dimensions else "resolucao pendente"
        duration_ms = int(metadata.get("duration_ms", 0))
        duration = f" | {duration_ms / 1000:.1f}s" if duration_ms else ""
        tags = f"\nTags: {', '.join(wallpaper.tags)}" if wallpaper.tags else ""
        resource = {"leve": "Leve", "medio": "Medio", "pesado": "Pesado"}.get(wallpaper.resource_class, "Leve")
        return f"{wallpaper.path}\n{wallpaper.category} | {resource} | {resolution}{duration} | {size_mb:.1f} MB{tags}"

    @staticmethod
    def _import_message(imported: list[WallpaperItem]) -> str:
        if not imported:
            return "Nenhum arquivo compativel foi importado."
        heavy = [item for item in imported if item.resource_class == "pesado"]
        medium = [item for item in imported if item.resource_class == "medio"]
        lines = [f"{len(imported)} arquivo(s) importado(s) para sua biblioteca pessoal."]
        if heavy:
            lines.append(f"{len(heavy)} pesado(s): o Movaura vai preferir copia otimizada para manter fluidez.")
        elif medium:
            lines.append(f"{len(medium)} medio(s): use o perfil Recomendado ou Leve se notar consumo alto.")
        analysis = analyze_media(imported[0].path)
        lines.append(f"Primeiro arquivo: {analysis.user_summary}.")
        return "\n".join(lines)

    @staticmethod
    def _set_combo_text(combo: QComboBox, text: str) -> None:
        index = combo.findText(text)
        if index >= 0:
            combo.setCurrentIndex(index)
