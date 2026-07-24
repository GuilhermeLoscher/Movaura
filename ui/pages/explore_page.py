from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus, urlparse

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.wallpaper_library import WallpaperItem, WallpaperLibrary
from core.settings import MovauraSettings


LOGGER = logging.getLogger(__name__)

CATEGORIES = (
    "Anime",
    "Cyberpunk",
    "Natureza",
    "Carros",
    "Minimalista",
    "Sci-Fi",
    "Abstrato",
    "Fantasia",
    "Espaco",
    "Cidades",
    "Gaming",
    "Escuro",
    "Claro",
    "Tecnologia",
)

SUPPORTED_FILE_FILTER = "Wallpapers (*.mp4 *.webm *.gif *.png *.jpg *.jpeg *.bmp *.webp)"


@dataclass(frozen=True)
class ExternalWallpaperSource:
    name: str
    domain: str
    search_template: str

    def search_url(self, query: str) -> str:
        encoded = quote_plus(query.strip())
        return self.search_template.format(query=encoded)


EXTERNAL_SOURCES = (
    ExternalWallpaperSource("Pexels", "www.pexels.com", "https://www.pexels.com/search/{query}/"),
    ExternalWallpaperSource("Pixabay", "pixabay.com", "https://pixabay.com/images/search/{query}/"),
    ExternalWallpaperSource("Unsplash", "unsplash.com", "https://unsplash.com/s/photos/{query}"),
    ExternalWallpaperSource("Wallhaven", "wallhaven.cc", "https://wallhaven.cc/search?q={query}"),
)


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
        self.last_imported: WallpaperItem | None = None
        self._remove_legacy_api_key()
        self._build_ui()
        self._connect_signals()
        self._load_settings()
        self._refresh_actions()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        title = QLabel("Explorar wallpapers")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        subtitle = QLabel("Encontre wallpapers em fontes externas, baixe pelo navegador e importe para o Movaura.")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar: cyberpunk city, anime landscape, space station...")
        self.search_edit.setMinimumHeight(30)
        root.addWidget(self.search_edit)

        category_title = QLabel("Categorias")
        category_title.setStyleSheet("font-weight: 600;")
        root.addWidget(category_title)
        category_grid = QGridLayout()
        category_grid.setHorizontalSpacing(8)
        category_grid.setVerticalSpacing(8)
        self.category_buttons: list[QPushButton] = []
        for index, category in enumerate(CATEGORIES):
            button = QPushButton(category)
            button.setMinimumHeight(30)
            button.clicked.connect(lambda checked=False, value=category: self._select_category(value))
            category_grid.addWidget(button, index // 4, index % 4)
            self.category_buttons.append(button)
        root.addLayout(category_grid)

        source_title = QLabel("Abrir pesquisa externa")
        source_title.setStyleSheet("font-weight: 600;")
        root.addWidget(source_title)
        source_row = QHBoxLayout()
        self.source_buttons: list[QPushButton] = []
        for source in EXTERNAL_SOURCES:
            button = QPushButton(source.name)
            button.setMinimumHeight(34)
            button.clicked.connect(lambda checked=False, current=source: self._open_source(current))
            source_row.addWidget(button)
            self.source_buttons.append(button)
        root.addLayout(source_row)

        self.notice_label = QLabel(
            "Confira a licenca e os termos da fonte antes de usar ou redistribuir o conteudo."
        )
        self.notice_label.setWordWrap(True)
        self.notice_label.setStyleSheet("padding: 8px; border: 1px solid #ddd; background: #fafafa;")
        root.addWidget(self.notice_label)

        import_title = QLabel("Importar para o Movaura")
        import_title.setStyleSheet("font-weight: 600;")
        root.addWidget(import_title)
        import_row = QHBoxLayout()
        self.import_button = QPushButton("Importar wallpaper")
        self.apply_button = QPushButton("Aplicar importado")
        self.favorite_button = QPushButton("Favoritar importado")
        self.open_library_button = QPushButton("Abrir biblioteca")
        for button in (self.import_button, self.apply_button, self.favorite_button, self.open_library_button):
            button.setMinimumHeight(34)
            import_row.addWidget(button)
        root.addLayout(import_row)

        self.status_label = QLabel("Pronto para explorar fontes externas oficiais.")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)
        root.addStretch(1)

    def _connect_signals(self) -> None:
        self.search_edit.textChanged.connect(self._save_search_text)
        self.search_edit.returnPressed.connect(lambda: self._open_source(EXTERNAL_SOURCES[0]))
        self.import_button.clicked.connect(self._import_wallpaper)
        self.apply_button.clicked.connect(self._apply_imported)
        self.favorite_button.clicked.connect(self._favorite_imported)
        self.open_library_button.clicked.connect(lambda: self.library_requested.emit(None))

    def _load_settings(self) -> None:
        self.search_edit.setText(self.settings.get_str("explore_last_query"))

    def _remove_legacy_api_key(self) -> None:
        if "pexels_api_key" in self.settings.data:
            self.settings.data.pop("pexels_api_key", None)
            self.settings.save()

    def _select_category(self, category: str) -> None:
        self.search_edit.setText(category)
        self.status_label.setText(f"Categoria selecionada: {category}. Escolha uma fonte externa para pesquisar.")
        self.status_changed.emit(f"Categoria selecionada: {category}.")

    def _open_source(self, source: ExternalWallpaperSource) -> None:
        query = self.search_edit.text().strip()
        if not query:
            self.status_label.setText("Digite uma busca ou escolha uma categoria antes de abrir uma fonte.")
            return
        url = source.search_url(query)
        if not self.is_allowed_external_url(url):
            self.status_label.setText("A fonte externa nao passou na validacao de seguranca.")
            LOGGER.warning("Blocked unapproved wallpaper source URL: %s", url)
            return
        opened = QDesktopServices.openUrl(QUrl(url))
        if not opened:
            self.status_label.setText("Nao foi possivel abrir o navegador padrao. Tente copiar a busca manualmente.")
            LOGGER.error("Could not open external wallpaper search URL: %s", url)
            return
        self._save_search_text()
        self.status_label.setText(f"Pesquisa aberta no navegador: {source.name}.")
        self.status_changed.emit(f"Pesquisa aberta no navegador: {source.name}.")

    def _import_wallpaper(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Importar wallpaper",
            str(Path.home()),
            SUPPORTED_FILE_FILTER,
        )
        if not paths:
            self.status_label.setText("Importacao cancelada.")
            return
        self.import_paths([Path(path) for path in paths])

    def import_paths(self, paths: list[Path]) -> list[WallpaperItem]:
        if not paths:
            self.status_label.setText("Importacao cancelada.")
            return []
        imported: list[WallpaperItem] = []
        skipped = 0
        for source in paths:
            if not source.is_file() or not self.library.kind_for_path(source):
                skipped += 1
                continue
            existing = self._existing_library_item_for_source(source)
            if existing:
                imported.append(existing)
                skipped += 1
                continue
            imported.extend(self.library.import_files([source]))
        if not imported:
            message = "Nenhum arquivo compativel foi importado."
            self.status_label.setText(message)
            return []
        self.last_imported = imported[0]
        if self.last_imported:
            self.library.mark_recent(self.last_imported)
        suffix = f" {skipped} arquivo(s) ignorado(s) por duplicidade ou formato invalido." if skipped else ""
        message = f"{len(imported)} wallpaper(s) disponivel(is) na biblioteca local.{suffix}"
        self.status_label.setText(message)
        self.status_changed.emit(message)
        self._refresh_actions()
        return imported

    def _apply_imported(self) -> None:
        if not self.last_imported:
            return
        self.wallpaper_selected.emit(self.last_imported)
        self.start_requested.emit()
        self.status_label.setText("Wallpaper importado aplicado.")

    def _favorite_imported(self) -> None:
        if not self.last_imported:
            return
        favorite = self.library.toggle_favorite(self.last_imported)
        self.status_label.setText("Wallpaper favoritado." if favorite else "Wallpaper removido dos favoritos.")

    def _save_search_text(self) -> None:
        self.settings.data["explore_last_query"] = self.search_edit.text().strip()
        self.settings.save()

    def _refresh_actions(self) -> None:
        has_import = self.last_imported is not None
        self.apply_button.setEnabled(has_import)
        self.favorite_button.setEnabled(has_import)

    def _existing_library_item_for_source(self, source: Path) -> WallpaperItem | None:
        source_digest = self._file_digest(source)
        if not source_digest:
            return None
        for item in self.library.items():
            if self._same_file(source, item.path):
                return item
            if item.path.name == source.name and item.path.stat().st_size == source.stat().st_size:
                current_digest = self._file_digest(item.path)
                if current_digest and current_digest == source_digest:
                    return item
        return None

    @staticmethod
    def is_allowed_external_url(url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            return False
        allowed_domains = {source.domain for source in EXTERNAL_SOURCES}
        return parsed.netloc.lower() in allowed_domains

    @staticmethod
    def build_external_url(source_name: str, query: str) -> str:
        for source in EXTERNAL_SOURCES:
            if source.name.lower() == source_name.lower():
                return source.search_url(query)
        raise ValueError("Fonte externa nao configurada.")

    @staticmethod
    def _same_file(first: Path, second: Path) -> bool:
        try:
            return first.resolve() == second.resolve()
        except OSError:
            return False

    @staticmethod
    def _file_digest(path: Path) -> str:
        try:
            digest = hashlib.sha256()
            with path.open("rb") as file:
                while chunk := file.read(1024 * 1024):
                    digest.update(chunk)
            return digest.hexdigest()
        except OSError:
            return ""
