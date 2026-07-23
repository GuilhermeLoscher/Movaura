from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QInputDialog,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.ai_generation.models import GenerationError, GenerationImage, GenerationRequest, GenerationResult
from core.ai_generation.prompting import QUALITY_LABELS, RESOLUTIONS, STYLES, enhance_prompt, style_by_id
from core.ai_generation.providers import MockImageGenerationProvider
from core.ai_generation.queue import GenerationQueue
from core.ai_generation.storage import GenerationHistoryStore, GenerationStorage
from core.playlist_manager import PlaylistEntry, PlaylistManager
from core.settings import MovauraSettings
from core.wallpaper_library import WallpaperItem, WallpaperLibrary


class AIGenerationPage(QWidget):
    wallpaper_selected = pyqtSignal(object)
    preview_requested = pyqtSignal()
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    library_requested = pyqtSignal(object)
    status_changed = pyqtSignal(str)

    def __init__(
        self,
        settings: MovauraSettings,
        library: WallpaperLibrary,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.library = library
        self.storage = GenerationStorage()
        self.history = GenerationHistoryStore()
        self.provider = MockImageGenerationProvider()
        self.queue = GenerationQueue(self.provider, self.storage, self.history, self)
        self.playlists = PlaylistManager()
        self.current_result: GenerationResult | None = None
        self.selected_image: GenerationImage | None = None
        self.last_saved_library_path: Path | None = None
        self.selected_history_item = None
        self.result_buttons: list[QPushButton] = []
        self._build_ui()
        self._connect_signals()
        self._load_settings()
        self._refresh_history()
        self._refresh_actions()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(6)

        header = QLabel("Criar com IA")
        header.setStyleSheet("font-size: 16px; font-weight: 600;")
        subtitle = QLabel(
            "Crie wallpapers localmente com o provedor mock. A arquitetura ja fica pronta para provedores reais depois."
        )
        subtitle.setWordWrap(True)
        root.addWidget(header)
        root.addWidget(subtitle)

        main = QHBoxLayout()
        main.setSpacing(10)
        root.addLayout(main, 1)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        left_scroll.setMinimumWidth(330)
        left_scroll.setMaximumWidth(480)
        left_panel = QWidget()
        left_panel.setMinimumWidth(310)
        left = QVBoxLayout(left_panel)
        left.setContentsMargins(0, 0, 8, 0)
        left.setSpacing(7)
        left_scroll.setWidget(left_panel)
        main.addWidget(left_scroll, 2)

        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setPlaceholderText("Exemplo: guerreira futurista em cidade neon, fundo limpo para icones")
        self.prompt_edit.setMinimumHeight(58)
        self.prompt_edit.setMaximumHeight(68)
        left.addWidget(QLabel("Descricao do wallpaper"))
        left.addWidget(self.prompt_edit)

        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(5)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.style_combo = QComboBox()
        for style in STYLES:
            self.style_combo.addItem(style.name, style.id)
        self.resolution_combo = QComboBox()
        for label, value in RESOLUTIONS.items():
            self.resolution_combo.addItem(label, value)
        self.resolution_combo.addItem("Usar resolucao do monitor", "monitor")
        self.resolution_combo.addItem("Personalizada", "custom")
        self.quality_combo = QComboBox()
        for value, label in QUALITY_LABELS.items():
            self.quality_combo.addItem(label, value)
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, self.provider.capabilities.max_images)
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 999999999)
        self.seed_spin.setSpecialValueText("Automatico")
        self.custom_width_spin = QSpinBox()
        self.custom_width_spin.setRange(320, 7680)
        self.custom_width_spin.setValue(1920)
        self.custom_height_spin = QSpinBox()
        self.custom_height_spin.setRange(240, 4320)
        self.custom_height_spin.setValue(1080)
        self.enhance_checkbox = QCheckBox("Melhorar prompt automaticamente")
        self.enhance_checkbox.setChecked(True)
        for widget in (
            self.style_combo,
            self.resolution_combo,
            self.quality_combo,
            self.quantity_spin,
            self.seed_spin,
            self.custom_width_spin,
            self.custom_height_spin,
        ):
            self._polish_input(widget)
        form.addRow("Estilo", self.style_combo)
        form.addRow("Resolucao", self.resolution_combo)
        form.addRow("Qualidade", self.quality_combo)
        form.addRow("Variacoes", self.quantity_spin)
        form.addRow("", self.enhance_checkbox)
        left.addLayout(form)

        advanced = QGroupBox("Avancado")
        self.advanced_group = advanced
        advanced.setCheckable(True)
        advanced.setChecked(False)
        advanced_outer = QVBoxLayout(advanced)
        advanced_outer.setContentsMargins(8, 8, 8, 8)
        self.advanced_body = QWidget()
        advanced_outer.addWidget(self.advanced_body)
        advanced_layout = QFormLayout(self.advanced_body)
        advanced_layout.setHorizontalSpacing(12)
        advanced_layout.setVerticalSpacing(8)
        self.negative_edit = QPlainTextEdit()
        self.negative_edit.setPlaceholderText("Exemplo: texto, marca d'agua, baixa nitidez")
        self.negative_edit.setMinimumHeight(72)
        self.negative_edit.setMaximumHeight(88)
        self.simulate_error_combo = QComboBox()
        for label, value in (
            ("Nenhum", ""),
            ("Erro de autenticacao", "auth"),
            ("Limite atingido", "rate_limit"),
            ("Timeout", "timeout"),
            ("Provedor indisponivel", "unavailable"),
            ("Resultado vazio", "empty"),
            ("Imagem invalida", "invalid"),
        ):
            self.simulate_error_combo.addItem(label, value)
        self._polish_input(self.simulate_error_combo)
        advanced_layout.addRow("Prompt negativo", self.negative_edit)
        advanced_layout.addRow("Seed", self.seed_spin)
        advanced_layout.addRow("Largura personalizada", self.custom_width_spin)
        advanced_layout.addRow("Altura personalizada", self.custom_height_spin)
        advanced_layout.addRow("Simular erro", self.simulate_error_combo)
        self.advanced_body.setVisible(False)
        left.addWidget(advanced)

        self.enhanced_prompt_label = QLabel("Prompt final sera exibido aqui.")
        self.enhanced_prompt_label.setWordWrap(True)
        self.enhanced_prompt_label.setMinimumHeight(44)
        self.enhanced_prompt_label.setStyleSheet("padding: 8px; border: 1px solid #ddd; background: #fafafa;")
        left.addWidget(self.enhanced_prompt_label)

        progress_row = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setMinimumHeight(28)
        self.status_label = QLabel("Pronto.")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(28)
        progress_row.addWidget(self.progress, 1)
        progress_row.addWidget(self.status_label, 1)
        footer = QVBoxLayout()
        footer.setSpacing(8)
        footer.addLayout(progress_row)

        action_grid = QGridLayout()
        self.generate_button = QPushButton("Gerar wallpaper")
        self.variation_button = QPushButton("Criar variacao")
        self.cancel_button = QPushButton("Cancelar")
        self.clear_button = QPushButton("Limpar resultado")
        self.preview_button = QPushButton("Pre-visualizar")
        self.apply_button = QPushButton("Aplicar")
        self.save_button = QPushButton("Salvar na biblioteca")
        self.favorite_button = QPushButton("Favoritar")
        self.playlist_button = QPushButton("Adicionar a playlist")
        self.open_library_button = QPushButton("Abrir biblioteca")
        self.delete_history_button = QPushButton("Excluir historico")
        self.stop_wallpaper_button = QPushButton("Parar/restaurar")
        for index, button in enumerate(
            (
                self.generate_button,
                self.variation_button,
                self.cancel_button,
                self.clear_button,
                self.preview_button,
                self.apply_button,
                self.save_button,
                self.favorite_button,
                self.playlist_button,
                self.open_library_button,
                self.delete_history_button,
                self.stop_wallpaper_button,
            )
        ):
            button.setMinimumHeight(34)
            action_grid.addWidget(button, index // 4, index % 4)
        for column in range(4):
            action_grid.setColumnStretch(column, 1)
        footer.addLayout(action_grid)
        left.addStretch(1)

        right = QVBoxLayout()
        right.setSpacing(6)
        main.addLayout(right, 3)
        right.addWidget(QLabel("Resultado pronto para usar"))
        self.results_area = QScrollArea()
        self.results_area.setWidgetResizable(True)
        self.results_area.setMinimumHeight(150)
        self.results_container = QWidget()
        self.results_grid = QGridLayout(self.results_container)
        self.results_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_area.setWidget(self.results_container)

        history_group = QGroupBox("Ver historico")
        self.history_group = history_group
        history_group.setCheckable(True)
        history_group.setChecked(False)
        history_layout = QVBoxLayout(history_group)
        self.history_body = QWidget()
        history_body_layout = QVBoxLayout(self.history_body)
        history_body_layout.setContentsMargins(0, 0, 0, 0)
        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(90)
        self.history_list.setMaximumHeight(150)
        self.history_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.history_list.setWordWrap(True)
        history_body_layout.addWidget(self.history_list)
        history_layout.addWidget(self.history_body)
        self.history_body.setVisible(False)

        right.addWidget(self.results_area, 1)
        right.addWidget(history_group)
        root.addLayout(footer)

    @staticmethod
    def _polish_input(widget: QWidget) -> None:
        widget.setMinimumHeight(28)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _connect_signals(self) -> None:
        self.generate_button.clicked.connect(self._generate)
        self.variation_button.clicked.connect(self._generate_variation)
        self.cancel_button.clicked.connect(self.queue.cancel)
        self.clear_button.clicked.connect(self._clear_current_result)
        self.preview_button.clicked.connect(self._preview_selected)
        self.apply_button.clicked.connect(self._apply_selected)
        self.save_button.clicked.connect(self._save_selected_to_library)
        self.favorite_button.clicked.connect(self._favorite_selected)
        self.playlist_button.clicked.connect(self._add_selected_to_playlist)
        self.open_library_button.clicked.connect(self._open_library)
        self.delete_history_button.clicked.connect(self._delete_selected_history)
        self.stop_wallpaper_button.clicked.connect(self.stop_requested.emit)
        self.advanced_group.toggled.connect(self.advanced_body.setVisible)
        self.history_group.toggled.connect(self.history_body.setVisible)
        self.prompt_edit.textChanged.connect(self._refresh_enhanced_prompt)
        self.negative_edit.textChanged.connect(self._refresh_enhanced_prompt)
        self.style_combo.currentIndexChanged.connect(self._refresh_enhanced_prompt)
        self.resolution_combo.currentIndexChanged.connect(self._refresh_enhanced_prompt)
        self.enhance_checkbox.toggled.connect(self._refresh_enhanced_prompt)
        self.history_list.itemClicked.connect(self._history_item_clicked)
        self.queue.progress.connect(self._progress_changed)
        self.queue.state_changed.connect(self._state_changed)
        self.queue.completed.connect(self._generation_completed)
        self.queue.failed.connect(self._generation_failed)
        self.queue.cancelled.connect(self._generation_cancelled)

    def _load_settings(self) -> None:
        self._set_combo_data(self.style_combo, self.settings.get_str("ai_generation_style") or "cinematic")
        self._set_combo_data(self.quality_combo, self.settings.get_str("ai_generation_quality") or "recommended")
        self._set_combo_text(self.resolution_combo, self.settings.get_str("ai_generation_resolution") or "Full HD 1920x1080")
        self.quantity_spin.setValue(max(1, min(4, self.settings.get_int("ai_generation_quantity") or 1)))
        self.enhance_checkbox.setChecked(self.settings.get_bool("ai_generation_auto_enhance"))
        self._refresh_enhanced_prompt()

    def _request_from_form(self) -> GenerationRequest:
        prompt = self.prompt_edit.toPlainText().strip()
        style_id = str(self.style_combo.currentData() or "cinematic")
        style = style_by_id(style_id)
        negative = self.negative_edit.toPlainText().strip()
        enhanced = enhance_prompt(prompt, style_id, negative) if self.enhance_checkbox.isChecked() else prompt
        resolution = self._selected_resolution()
        quality = str(self.quality_combo.currentData() or "recommended")
        seed = self.seed_spin.value() or None
        return GenerationRequest(
            prompt=prompt,
            enhanced_prompt=enhanced,
            negative_prompt=negative,
            style_id=style.id,
            style_name=style.name,
            resolution=(int(resolution[0]), int(resolution[1])),
            quantity=self.quantity_spin.value(),
            quality=quality,
            seed=seed,
            provider_id=self.provider.capabilities.name,
            simulate_error=str(self.simulate_error_combo.currentData() or ""),
        )

    def _selected_resolution(self) -> tuple[int, int]:
        value = self.resolution_combo.currentData()
        if value == "monitor":
            screen = QApplication.primaryScreen()
            if screen:
                size = screen.size()
                return max(320, int(size.width())), max(240, int(size.height()))
            return (1920, 1080)
        if value == "custom":
            return (self.custom_width_spin.value(), self.custom_height_spin.value())
        return (int(value[0]), int(value[1])) if isinstance(value, tuple) else (1920, 1080)

    def _generate(self) -> None:
        request = self._request_from_form()
        if not request.prompt:
            QMessageBox.information(self, "Criar com IA", "Descreva o wallpaper antes de gerar.")
            return
        self._start_generation(request)

    def _generate_variation(self) -> None:
        if self.selected_history_item:
            self._load_history_item(self.selected_history_item)
        request = self._request_from_form()
        if not request.prompt:
            QMessageBox.information(self, "Criar variacao", "Selecione um item do historico ou descreva o wallpaper.")
            return
        seed = self._new_variation_seed(request.seed)
        self.seed_spin.setValue(seed)
        varied = GenerationRequest(
            prompt=request.prompt,
            enhanced_prompt=request.enhanced_prompt,
            negative_prompt=request.negative_prompt,
            style_id=request.style_id,
            style_name=request.style_name,
            resolution=request.resolution,
            quantity=request.quantity,
            quality=request.quality,
            seed=seed,
            provider_id=request.provider_id,
            simulate_error=request.simulate_error,
            source_image=str(self.selected_image.path) if self.selected_image else "",
            metadata=dict(request.metadata),
        )
        self._start_generation(varied)

    def _start_generation(self, request: GenerationRequest) -> None:
        self.settings.data.update(
            {
                "ai_generation_provider": request.provider_id,
                "ai_generation_style": request.style_id,
                "ai_generation_quality": request.quality,
                "ai_generation_resolution": self.resolution_combo.currentText(),
                "ai_generation_quantity": request.quantity,
                "ai_generation_auto_enhance": self.enhance_checkbox.isChecked(),
            }
        )
        self.settings.save()
        self.current_result = None
        self.selected_image = None
        self.last_saved_library_path = None
        self._clear_results()
        self.progress.setValue(0)
        if not self.queue.start(request):
            self.status_label.setText("Ja existe uma geracao em andamento.")
        self._refresh_actions()

    @staticmethod
    def _new_variation_seed(current: int | None) -> int:
        base = current or 0
        tick = int(datetime.now(timezone.utc).timestamp() * 1000) % 1_000_000_000
        return (base + tick + 104729) % 1_000_000_000 or 1

    def _progress_changed(self, value: int, message: str) -> None:
        self.progress.setValue(value)
        self.status_label.setText(message)

    def _state_changed(self, state: str, message: str) -> None:
        self.status_label.setText(message)
        self.status_changed.emit(message)
        self._refresh_actions()

    def _generation_completed(self, result: object) -> None:
        if not isinstance(result, GenerationResult):
            return
        self.current_result = result
        self.selected_image = result.images[0] if result.images else None
        self.progress.setValue(100)
        self._show_results(result.images)
        if self.selected_image:
            self.status_label.setText("Wallpaper gerado e selecionado. Clique em Aplicar ou Salvar na biblioteca.")
            self.status_changed.emit("Wallpaper gerado e selecionado.")
        else:
            self.status_label.setText(f"{len(result.images)} wallpaper(s) gerado(s).")
        self._refresh_history()
        self._refresh_actions()

    def _generation_failed(self, error: object) -> None:
        message = error.user_message if isinstance(error, GenerationError) else str(error)
        self.status_label.setText(message)
        QMessageBox.warning(self, "Criar com IA", message)
        self._refresh_history()
        self._refresh_actions()

    def _generation_cancelled(self, message: str) -> None:
        self.status_label.setText(message)
        self.progress.setValue(0)
        self._refresh_actions()

    def _show_results(self, images: list[GenerationImage]) -> None:
        self._clear_results()
        for index, image in enumerate(images):
            button = QPushButton()
            button.setCheckable(True)
            button.setStyleSheet("QPushButton:checked { border: 3px solid #0078d4; background: #eef6ff; }")
            button.setIcon(QIcon(QPixmap(str(image.path)).scaled(250, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            button.setIconSize(QSize(250, 140))
            button.setMinimumSize(270, 170)
            button.setText(f"Variacao {index + 1}\n{image.width}x{image.height}")
            button.setProperty("image_path", str(image.path))
            button.clicked.connect(lambda checked=False, img=image: self._select_result(img))
            self.results_grid.addWidget(button, index // 2, index % 2)
            self.result_buttons.append(button)
        if images:
            self._select_result(images[0])

    def _clear_results(self) -> None:
        while self.results_grid.count():
            item = self.results_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.result_buttons = []

    def _clear_current_result(self) -> None:
        if self.queue.is_running:
            return
        self.current_result = None
        self.selected_image = None
        self._clear_results()
        self.progress.setValue(0)
        self.status_label.setText("Resultado limpo. Descreva ou ajuste o prompt e gere outro wallpaper.")
        self.status_changed.emit("Resultado limpo.")
        self._refresh_actions()

    def _select_result(self, image: GenerationImage) -> None:
        self.selected_image = image
        for button in self.result_buttons:
            button.setChecked(button.property("image_path") == str(image.path))
        self.status_label.setText(f"Selecionado automaticamente: {image.path.name}")
        self._refresh_actions()

    def _preview_selected(self) -> None:
        item = self._selected_as_library_item()
        if item:
            self.wallpaper_selected.emit(item)
            self.preview_requested.emit()

    def _apply_selected(self) -> None:
        item = self._selected_as_library_item()
        if item:
            self.wallpaper_selected.emit(item)
            self.start_requested.emit()

    def _save_selected_to_library(self) -> None:
        item = self._persist_selected_to_library()
        if item:
            self.wallpaper_selected.emit(item)
            self.status_label.setText("Wallpaper salvo na biblioteca.")
            self.status_changed.emit("Wallpaper salvo na biblioteca.")
            self._refresh_history()

    def _persist_selected_to_library(self) -> WallpaperItem | None:
        if not self.selected_image:
            return
        existing = self._library_item_for_path(self.selected_image.path)
        if existing:
            self.last_saved_library_path = existing.path
            return existing
        imported = self.library.import_files([self.selected_image.path])
        if imported:
            self.library.update_details(imported[0], ["ia", "movaura", "mock"], "Criados com IA", "leve")
            self.last_saved_library_path = imported[0].path
            return imported[0]
        QMessageBox.warning(self, "Criar com IA", "Nao foi possivel salvar o wallpaper na biblioteca.")
        return None

    def _favorite_selected(self) -> None:
        item = self._library_item_for_path(self.last_saved_library_path or Path())
        if item:
            self.library.toggle_favorite(item)
            self.status_label.setText("Favorito atualizado.")
            return
        QMessageBox.information(self, "Favoritar", "Salve o wallpaper na biblioteca antes de favoritar.")

    def _add_selected_to_playlist(self) -> None:
        item = self._persist_selected_to_library()
        if not item:
            return
        names = self.playlists.names()
        active = self.settings.get_str("active_playlist") or "default"
        name, ok = QInputDialog.getItem(
            self,
            "Adicionar a playlist",
            "Playlist",
            names,
            max(0, names.index(active)) if active in names else 0,
            False,
        )
        if not ok or not name:
            return
        entries = self.playlists.entries(name)
        if not any(Path(entry.path) == item.path for entry in entries):
            entries.append(PlaylistEntry(str(item.path), 60))
            self.playlists.save(name, entries)
        self.status_label.setText(f"Wallpaper adicionado a playlist {name}.")

    def _open_library(self) -> None:
        self.library_requested.emit(self.last_saved_library_path)

    def _selected_as_library_item(self) -> WallpaperItem | None:
        if not self.selected_image or not self.selected_image.path.is_file():
            return None
        return WallpaperItem(
            kind="image",
            path=self.selected_image.path,
            name=self.selected_image.path.stem.replace("-", " ").title(),
            included=False,
            favorite=False,
            recent=False,
            tags=("ia", "movaura", "mock"),
            collection="Criados com IA",
            resource_class="leve",
        )

    def _library_item_for_path(self, path: Path) -> WallpaperItem | None:
        if not path:
            return None
        try:
            target = path.resolve()
        except OSError:
            target = path
        for item in self.library.items():
            try:
                current = item.path.resolve()
            except OSError:
                current = item.path
            if current == target:
                return item
        return None

    def _refresh_history(self) -> None:
        self.history_list.clear()
        for item in self.history.items()[:30]:
            seed = f" | seed {item.seed}" if item.seed is not None else ""
            text = f"{item.created_at[:19].replace('T', ' ')} | {item.style_name} | {item.status}{seed}\n{item.prompt[:120]}"
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.history_list.addItem(list_item)

    def _history_item_clicked(self, list_item: QListWidgetItem) -> None:
        item = list_item.data(Qt.ItemDataRole.UserRole)
        if item:
            self.selected_history_item = item
            self._load_history_item(item)

    def _load_history_item(self, item) -> None:
        self.prompt_edit.setPlainText(item.prompt)
        self.negative_edit.setPlainText(getattr(item, "negative_prompt", "") or "")
        self._set_combo_data(self.style_combo, item.style_id)
        self._set_combo_data(self.quality_combo, item.quality)
        self._set_resolution_from_history(item.resolution)
        self.seed_spin.setValue(int(item.seed or 0))
        images = [
            GenerationImage(
                path=Path(path),
                width=self._selected_resolution()[0],
                height=self._selected_resolution()[1],
                seed=int(item.seed or 0),
                prompt=item.enhanced_prompt or item.prompt,
                metadata={"history_id": item.id},
            )
            for path in item.images
            if Path(path).is_file()
        ]
        if images:
            self.current_result = GenerationResult(item.provider_id, self._request_from_form(), images)
            self.selected_image = images[0]
            self._show_results(images)
        self.status_label.setText("Historico carregado. Voce pode aplicar, salvar ou criar variacao.")
        self._refresh_actions()

    def _delete_selected_history(self) -> None:
        list_item = self.history_list.currentItem()
        if not list_item:
            QMessageBox.information(self, "Historico", "Selecione um item do historico para excluir.")
            return
        item = list_item.data(Qt.ItemDataRole.UserRole)
        protected = {str(library_item.path) for library_item in self.library.items()}
        if self.history.delete_item(item.id, protected):
            if self.selected_history_item and self.selected_history_item.id == item.id:
                self.selected_history_item = None
            self._refresh_history()
            self.status_label.setText("Item do historico excluido.")

    def _set_resolution_from_history(self, value: str) -> None:
        for index in range(self.resolution_combo.count()):
            data = self.resolution_combo.itemData(index)
            if isinstance(data, tuple) and value == f"{data[0]}x{data[1]}":
                self.resolution_combo.setCurrentIndex(index)
                return
        if "x" in value:
            try:
                width, height = [int(part) for part in value.lower().split("x", 1)]
            except ValueError:
                return
            self.custom_width_spin.setValue(width)
            self.custom_height_spin.setValue(height)
            self._set_combo_data(self.resolution_combo, "custom")

    def _refresh_actions(self) -> None:
        running = self.queue.is_running
        has_selection = self.selected_image is not None
        has_history_selection = self.history_list.currentItem() is not None
        self.generate_button.setEnabled(not running)
        self.variation_button.setEnabled((has_selection or self.selected_history_item is not None) and not running)
        self.cancel_button.setEnabled(running)
        self.clear_button.setEnabled(has_selection and not running)
        self.preview_button.setEnabled(has_selection and not running)
        self.apply_button.setEnabled(has_selection and not running)
        self.save_button.setEnabled(has_selection and not running)
        self.favorite_button.setEnabled(has_selection and not running)
        self.playlist_button.setEnabled(has_selection and not running)
        self.delete_history_button.setEnabled(has_history_selection and not running)

    def _refresh_enhanced_prompt(self) -> None:
        request = self._request_from_form()
        self.enhanced_prompt_label.setText(f"Prompt final: {request.final_prompt or 'descreva o wallpaper acima.'}")

    @staticmethod
    def _set_combo_data(combo: QComboBox, value: str) -> None:
        for index in range(combo.count()):
            if str(combo.itemData(index)) == value:
                combo.setCurrentIndex(index)
                return

    @staticmethod
    def _set_combo_text(combo: QComboBox, text: str) -> None:
        for index in range(combo.count()):
            if combo.itemText(index) == text:
                combo.setCurrentIndex(index)
                return

    def shutdown(self) -> None:
        self.queue.shutdown()
