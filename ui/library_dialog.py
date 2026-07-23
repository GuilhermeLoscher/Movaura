from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFileIconProvider,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QInputDialog,
    QVBoxLayout,
)

from core.media_analyzer import analyze_media
from core.wallpaper_library import WallpaperItem, WallpaperLibrary
from core.thumbnail_cache import ThumbnailCache, image_dimensions


FILTERS = {
    "Todos": "",
    "Imagens": "image",
    "GIFs": "gif",
    "Videos": "video",
    "Favoritos": "favorite",
    "Recentes": "recent",
    "Importados": "personal",
    "Leves": "leve",
    "Medios": "medio",
    "Pesados": "pesado",
    "4K": "4k",
}
SORTS = ("Nome", "Recentes primeiro", "Favoritos primeiro")


class LibraryDialog(QDialog):
    selected = pyqtSignal(object)
    preview_requested = pyqtSignal(object)

    def __init__(self, library: WallpaperLibrary, parent=None, initial_path: Path | None = None) -> None:
        super().__init__(parent)
        self.library = library
        self.initial_path = initial_path
        self.thumbnails = ThumbnailCache(self)
        self.thumbnails.ready.connect(lambda _: self.refresh())
        self.setWindowTitle("Biblioteca de wallpapers")
        self.resize(940, 650)
        self.setAcceptDrops(True)
        self._build_ui()
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
        toolbar.addWidget(self.search_edit, 1)
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
        root.addWidget(self.list_widget, 1)

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

    def refresh(self) -> None:
        search = self.search_edit.text().strip().lower()
        current_filter = FILTERS[self.filter_combo.currentText()]
        self.list_widget.clear()
        wallpapers = self.library.items()
        if self.sort_combo.currentText() == "Recentes primeiro":
            wallpapers.sort(key=lambda item: (self.library.recent_rank(item), item.name.lower()))
        elif self.sort_combo.currentText() == "Favoritos primeiro":
            wallpapers.sort(key=lambda item: (not item.favorite, item.name.lower()))
        for wallpaper in wallpapers:
            searchable = " ".join((wallpaper.name, wallpaper.collection, *wallpaper.tags)).lower()
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
            if current_filter and current_filter not in {"favorite", "personal", "recent", "leve", "medio", "pesado", "4k"}:
                if wallpaper.kind != current_filter:
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
        self._selection_changed()

    def _import_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Importar pasta de wallpapers", str(Path.home()))
        if not folder:
            return
        imported = self.library.import_folder(Path(folder))
        self.refresh()
        QMessageBox.information(self, "Importacao concluida", self._import_message(imported))

    def _import_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Importar wallpapers",
            str(Path.home()),
            "Wallpapers (*.mp4 *.webm *.gif *.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not paths:
            return
        imported = self.library.import_files([Path(path) for path in paths])
        self.refresh()
        QMessageBox.information(
            self,
            "Importacao concluida",
            self._import_message(imported),
        )

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

    def _selected(self) -> WallpaperItem | None:
        items = self.list_widget.selectedItems()
        return items[0].data(Qt.ItemDataRole.UserRole) if items else None

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        imported = self.library.import_files([path for path in paths if path.is_file()])
        for folder in [path for path in paths if path.is_dir()]:
            imported.extend(self.library.import_folder(folder))
        self.refresh()
        if imported:
            QMessageBox.information(
                self,
                "Importação concluída",
                f"{len(imported)} arquivo(s) adicionado(s) à sua biblioteca.",
            )
        event.acceptProposedAction()

    @staticmethod
    def _label(wallpaper: WallpaperItem) -> str:
        favorite = " ★" if wallpaper.favorite else ""
        source = "incluido" if wallpaper.included else "importado"
        collection = f" | {wallpaper.collection}" if wallpaper.collection else ""
        resource = {"leve": "Leve", "medio": "Medio", "pesado": "Pesado"}.get(wallpaper.resource_class, "Leve")
        return f"{wallpaper.name}{favorite}\n{source}{collection} | {resource}"

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
        return f"{wallpaper.path}\n{resource} | {resolution}{duration} | {size_mb:.1f} MB{tags}"

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
