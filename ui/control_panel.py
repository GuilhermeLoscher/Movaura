"""Movaura control panel. Desenvolvido por Guilherme Loscher (GL)."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from threading import Thread

from PyQt6.QtCore import QObject, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.app_logging import log_path
from core.benchmark import BenchmarkResult, run_benchmark
from core.app_rule_manager import AppRuleManager
from core.catalog import OnlineCatalog
from core.engine import MovauraEngine
from core.media_analyzer import analyze_media
from core.monitor_manager import MonitorManager
from core.native_compositor import NativeCompositorLauncher
from core.power_status import PowerStatusReader
from core.playlist_manager import PlaylistManager
from core.performance_advisor import PerformanceAdvisor
from core.performance_monitor import PerformanceSnapshot
from core.presentation_backend import PresentationBackend
from core.presentation_validator import PresentationValidator
from core.profile_manager import ProfileManager
from core.runtime_paths import app_icon_path, app_logo_path, app_root
from core.settings import MovauraSettings
from core.screensaver import ScreensaverManager
from core.startup_manager import StartupManager
from core.support_report import create_support_report
from core.version import APP_AUTHOR_SIGNATURE
from core.system_wallpaper import SystemWallpaperBackend
from core.update_checker import UpdateChecker, UpdateResult
from core.wallpaper_library import WallpaperItem, WallpaperLibrary
from ui.ai_generation_page import AIGenerationPage
from ui.library_dialog import LibraryDialog
from ui.product_dialogs import AppRulesDialog, CatalogDialog, MonitorProfilesDialog, PlaylistDialog, QuickCreateDialog, SceneEditorDialog


EXPERIENCE_MODES = {
    "Papel de parede estático": "desktop-static",
    "Área de trabalho animada": "animated-desktop",
    "Pré-visualização animada": "animated-preview",
    "Teste em tela cheia": "fullscreen-test",
}
RENDERERS = {
    "Cor": "color",
    "Imagem": "image",
    "Vídeo": "video",
    "GIF": "gif",
    "OpenGL": "opengl",
    "Parallax suave": "parallax",
    "Visualizador de áudio": "audio",
    "Particulas leves": "particles",
    "Chuva": "rain",
    "Neblina": "fog",
    "Brilho suave": "glow",
    "Vinheta": "vignette",
    "Pulso de exemplo": "sample_pulse",
}
MODE_RENDERERS = {
    "desktop-static": {"color", "image"},
    "animated-desktop": set(RENDERERS.values()),
    "animated-preview": set(RENDERERS.values()),
    "fullscreen-test": set(RENDERERS.values()),
}
WALLPAPER_POSITIONS = {
    "Preencher": "fill",
    "Ajustar": "fit",
    "Esticar": "stretch",
    "Centralizar": "center",
    "Lado a lado": "tile",
    "Expandir entre monitores": "span",
}
PERFORMANCE_PROFILES = {
    "Recomendado": {"id": "adaptive", "fps": 30, "low_power_mode": True},
    "Leve": {"id": "economy", "fps": 15, "low_power_mode": True},
    "Máxima qualidade": {"id": "quality", "fps": 60, "low_power_mode": False},
}
SURFACE_LABELS = {
    "preview": "pré-visualização",
    "fullscreen": "tela cheia",
    "desktop-live": "área de trabalho",
}
MULTI_MONITOR_MODES = {
    "Repetir em cada monitor": "repeat",
    "Panorâmico entre monitores": "span",
}


class BackgroundOperation(QObject):
    finished = pyqtSignal(object)


class ControlPanel(QWidget):
    def __init__(self, app: QApplication, settings: MovauraSettings) -> None:
        super().__init__()
        self.app = app
        self.settings = settings
        self.profile_manager = ProfileManager()
        self.monitor_manager = MonitorManager()
        self.power_status = PowerStatusReader()
        self.performance_advisor = PerformanceAdvisor()
        self.validator = PresentationValidator()
        self.startup_manager = StartupManager()
        self.library = WallpaperLibrary()
        self.update_checker = UpdateChecker()
        self.playlists = PlaylistManager()
        self.app_rules = AppRuleManager()
        self.catalog = OnlineCatalog()
        self.screensaver = ScreensaverManager()
        self.preview_launcher = NativeCompositorLauncher()
        self.engine: MovauraEngine | None = None
        self.wallpaper_operation: BackgroundOperation | None = None
        self.support_operation: BackgroundOperation | None = None
        self.update_operation: BackgroundOperation | None = None
        self.pending_update: UpdateResult | None = None
        self.benchmark_operation: BackgroundOperation | None = None
        self._restoring_move_size = False
        self._normal_window_size: QSize | None = None
        self._move_resize_guard = QTimer(self)
        self._move_resize_guard.setSingleShot(True)
        self._move_resize_guard.setInterval(120)
        self._move_resize_guard.timeout.connect(self._restore_size_after_move)
        self._geometry_guard = QTimer(self)
        self._geometry_guard.setInterval(250)
        self._geometry_guard.timeout.connect(self._restore_size_after_move)

        self.setWindowTitle("Movaura")
        self.setWindowIcon(QIcon(str(app_icon_path())))
        self.setMinimumSize(700, 520)
        self._build_ui()
        self._fit_to_current_screen()
        self._refresh_profiles()
        self._load_settings_to_form()
        self._refresh_power_status()
        self.power_timer = QTimer(self)
        self.power_timer.setInterval(5000)
        self.power_timer.timeout.connect(self._refresh_power_status)
        self.power_timer.start()
        self.performance_timer = QTimer(self)
        self.performance_timer.setInterval(3000)
        self.performance_timer.timeout.connect(self._refresh_performance_status)
        self.performance_timer.start()
        self._geometry_guard.start()

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        if self._restoring_move_size or self.isMaximized() or self.isFullScreen():
            return
        self._move_resize_guard.start()
        QTimer.singleShot(350, self._restore_size_after_move)
        QTimer.singleShot(900, self._restore_size_after_move)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._restoring_move_size or self.isMaximized() or self.isFullScreen() or self._normal_window_size is None:
            return
        current = self.size()
        if (
            current.width() > self._normal_window_size.width() + 8
            or current.height() > self._normal_window_size.height() + 8
        ):
            self._move_resize_guard.start()
            QTimer.singleShot(350, self._restore_size_after_move)
            QTimer.singleShot(900, self._restore_size_after_move)

    def _restore_size_after_move(self) -> None:
        if self.isMaximized() or self.isFullScreen() or self._normal_window_size is None:
            return
        screen = self.screen() or self.app.primaryScreen()
        if not screen:
            return
        available = screen.availableGeometry()
        target_width = min(self._normal_window_size.width(), max(self.minimumWidth(), available.width() - 40))
        target_height = min(self._normal_window_size.height(), max(self.minimumHeight(), available.height() - 40))
        target = QSize(target_width, target_height)
        if self.size() == target:
            return
        self._restoring_move_size = True
        self.resize(target)
        self._restoring_move_size = False

    def _fit_to_current_screen(self) -> None:
        screen = self.app.primaryScreen()
        if not screen:
            self.resize(900, 600)
            self._normal_window_size = QSize(900, 600)
            self.setMaximumSize(self._normal_window_size)
            return
        available = screen.availableGeometry()
        width = min(940, max(700, available.width() - 180))
        height = min(620, max(520, available.height() - 120))
        self.resize(width, height)
        self._normal_window_size = QSize(width, height)
        self.setMaximumSize(self._normal_window_size)
        self.move(
            available.x() + max(20, (available.width() - width) // 2),
            available.y() + max(20, (available.height() - height) // 2),
        )

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        header = QHBoxLayout()
        logo = QLabel()
        logo.setFixedSize(52, 52)
        logo.setPixmap(QPixmap(str(app_logo_path())).scaled(52, 52))
        header.addWidget(logo)
        title = QLabel("Movaura")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        header.addWidget(title)
        header.addStretch(1)
        root.addLayout(header)

        tabs = QTabWidget()
        tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        tabs.setMaximumHeight(470)
        self.tabs = tabs
        root.addWidget(tabs, 1)
        wallpaper_tab = QWidget()
        quick_tab = QWidget()
        settings_tab = QWidget()
        support_tab = QWidget()
        automation_tab = QWidget()
        ai_tab = AIGenerationPage(self.settings, self.library, self)
        self.ai_generation_page = ai_tab
        tabs.addTab(quick_tab, "Início")
        tabs.addTab(wallpaper_tab, "Wallpaper")
        tabs.addTab(ai_tab, "Criar com IA")
        tabs.addTab(settings_tab, "Desempenho")
        tabs.addTab(automation_tab, "Automação")
        tabs.addTab(support_tab, "Suporte")

        quick_layout = QVBoxLayout(quick_tab)
        quick_layout.setContentsMargins(12, 12, 12, 12)
        quick_layout.setSpacing(8)
        self.quick_headline_label = QLabel("Comece por aqui")
        self.quick_headline_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.quick_subtitle_label = QLabel("Escolha, pré-visualize e aplique um wallpaper sem mexer em opções técnicas.")
        self.quick_subtitle_label.setWordWrap(True)
        self.quick_recommendation_label = QLabel("Pronto para aplicar.")
        self.quick_recommendation_label.setWordWrap(True)
        self.quick_recommendation_label.setMinimumHeight(42)
        self.quick_recommendation_label.setStyleSheet("padding: 8px; border: 1px solid #ddd; background: #fafafa;")
        quick_layout.addWidget(self.quick_headline_label)
        quick_layout.addWidget(self.quick_subtitle_label)
        quick_layout.addWidget(self.quick_recommendation_label)
        quick_summary = QGridLayout()
        quick_summary.setHorizontalSpacing(12)
        quick_summary.setVerticalSpacing(6)
        self.quick_wallpaper_label = QLabel("Nenhum wallpaper selecionado")
        self.quick_screen_combo = QComboBox()
        self.quick_performance_label = QLabel("Compositor parado")
        self.quick_state_label = QLabel("Parado")
        self.quick_setup_label = QLabel("")
        for value_label in (
            self.quick_wallpaper_label,
            self.quick_performance_label,
            self.quick_state_label,
            self.quick_setup_label,
        ):
            value_label.setMinimumHeight(24)
            value_label.setWordWrap(True)
            value_label.setStyleSheet("padding: 2px 0;")
        self.quick_screen_combo.setMinimumHeight(28)
        self.quick_screen_combo.setMinimumWidth(220)
        for row, (caption, widget) in enumerate(
            (
                ("1. Wallpaper", self.quick_wallpaper_label),
                ("2. Tela", self.quick_screen_combo),
                ("3. Desempenho", self.quick_performance_label),
                ("Resumo", self.quick_setup_label),
                ("Estado atual", self.quick_state_label),
            )
        ):
            caption_label = QLabel(caption)
            caption_label.setMinimumHeight(24)
            caption_label.setStyleSheet("font-weight: 600;")
            quick_summary.addWidget(caption_label, row, 0)
            quick_summary.addWidget(widget, row, 1)
        quick_summary.setColumnStretch(1, 1)
        quick_layout.addLayout(quick_summary)
        self.quick_library_button = QPushButton("Escolher na biblioteca")
        self.quick_create_button = QPushButton("Criar com efeitos e áudio")
        self.quick_preview_button = QPushButton("Pré-visualizar")
        self.quick_stop_preview_button = QPushButton("Fechar pré-visualização")
        self.quick_start_button = QPushButton("Aplicar na área de trabalho")
        self.quick_optimize_button = QPushButton("Corrigir desempenho automaticamente")
        self.quick_catalog_button = QPushButton("Abrir catálogo")
        self.quick_benchmark_button = QPushButton("Medir desempenho")
        self.quick_advanced_button = QPushButton("Ajustes avançados")
        self.quick_pause_button = QPushButton("Pausar ou continuar")
        self.quick_stop_button = QPushButton("Parar")
        quick_buttons = (
            self.quick_library_button,
            self.quick_create_button,
            self.quick_preview_button,
            self.quick_stop_preview_button,
            self.quick_start_button,
            self.quick_optimize_button,
            self.quick_catalog_button,
            self.quick_benchmark_button,
            self.quick_advanced_button,
            self.quick_pause_button,
            self.quick_stop_button,
        )
        button_grid = QGridLayout()
        button_grid.setHorizontalSpacing(10)
        button_grid.setVerticalSpacing(8)
        for index, button in enumerate(quick_buttons):
            button.setMinimumHeight(38)
            button.setMinimumWidth(0)
            button_grid.addWidget(button, index // 2, index % 2)
        button_grid.setColumnStretch(0, 1)
        button_grid.setColumnStretch(1, 1)
        quick_layout.addLayout(button_grid)
        quick_layout.addStretch(1)

        wallpaper_layout = QVBoxLayout(wallpaper_tab)
        wallpaper_form = QFormLayout()
        wallpaper_layout.addLayout(wallpaper_form)

        self.profile_combo = QComboBox()
        profile_buttons = QHBoxLayout()
        for text, callback in (
            ("Carregar", self._load_selected_profile),
            ("Novo", self._new_profile),
            ("Salvar", self._save_current_profile),
            ("Excluir", self._delete_selected_profile),
        ):
            button = QPushButton(text)
            button.clicked.connect(callback)
            profile_buttons.addWidget(button)
        profile_row = QHBoxLayout()
        profile_row.addWidget(self.profile_combo, 1)
        profile_row.addLayout(profile_buttons)
        wallpaper_form.addRow("Perfil", profile_row)
        self.active_playlist_label = QLabel()
        wallpaper_form.addRow("Playlist ativa", self.active_playlist_label)

        self.experience_combo = QComboBox()
        self.experience_combo.addItems(EXPERIENCE_MODES)
        wallpaper_form.addRow("Modo", self.experience_combo)
        self.renderer_combo = QComboBox()
        wallpaper_form.addRow("Renderizador", self.renderer_combo)
        self.screen_combo = QComboBox()
        wallpaper_form.addRow("Monitor", self.screen_combo)
        self.multi_monitor_combo = QComboBox()
        self.multi_monitor_combo.addItems(MULTI_MONITOR_MODES)
        wallpaper_form.addRow("Vários monitores", self.multi_monitor_combo)
        self.monitor_profiles_button = QPushButton("Configurar wallpapers por tela")
        wallpaper_form.addRow("", self.monitor_profiles_button)
        self.wallpaper_position_combo = QComboBox()
        self.wallpaper_position_combo.addItems(WALLPAPER_POSITIONS)
        wallpaper_form.addRow("Posição da imagem", self.wallpaper_position_combo)

        self.media_path_edit = QLineEdit()
        self.browse_button = QPushButton("Procurar")
        self.gallery_button = QPushButton("Biblioteca visual")
        media_row = QHBoxLayout()
        media_row.addWidget(self.media_path_edit, 1)
        media_row.addWidget(self.browse_button)
        media_row.addWidget(self.gallery_button)
        wallpaper_form.addRow("Arquivo de mídia", media_row)

        self.color_edit = QLineEdit()
        self.color_button = QPushButton("Escolher")
        color_row = QHBoxLayout()
        color_row.addWidget(self.color_edit, 1)
        color_row.addWidget(self.color_button)
        wallpaper_form.addRow("Cor", color_row)

        actions = QHBoxLayout()
        self.apply_button = QPushButton("Salvar")
        self.start_button = QPushButton("Iniciar")
        self.stop_button = QPushButton("Parar")
        self.restore_button = QPushButton("Restaurar anterior")
        for button in (self.apply_button, self.start_button, self.stop_button, self.restore_button):
            actions.addWidget(button)
        wallpaper_layout.addLayout(actions)

        performance_form = QFormLayout(settings_tab)
        self.performance_combo = QComboBox()
        self.performance_combo.addItems(PERFORMANCE_PROFILES)
        performance_form.addRow("Perfil de desempenho", self.performance_combo)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        performance_form.addRow("FPS máximo", self.fps_spin)
        self.pause_fullscreen_checkbox = QCheckBox("Pausar animações durante tela cheia")
        performance_form.addRow("", self.pause_fullscreen_checkbox)
        self.low_power_checkbox = QCheckBox("Reduzir FPS automaticamente ao usar bateria")
        performance_form.addRow("", self.low_power_checkbox)
        self.optimize_videos_checkbox = QCheckBox("Otimizar vídeos pesados automaticamente")
        performance_form.addRow("", self.optimize_videos_checkbox)
        self.auto_performance_checkbox = QCheckBox("Assistente inteligente: reduzir consumo automaticamente")
        performance_form.addRow("", self.auto_performance_checkbox)
        self.auto_cpu_spin = QSpinBox()
        self.auto_cpu_spin.setRange(5, 95)
        self.auto_cpu_spin.setSuffix("%")
        performance_form.addRow("Limite de CPU para agir", self.auto_cpu_spin)
        self.auto_memory_spin = QSpinBox()
        self.auto_memory_spin.setRange(64, 4096)
        self.auto_memory_spin.setSuffix(" MB")
        performance_form.addRow("Limite de RAM para agir", self.auto_memory_spin)
        self.tray_checkbox = QCheckBox("Ativar ícone na bandeja")
        performance_form.addRow("", self.tray_checkbox)
        self.plugins_checkbox = QCheckBox("Ativar plugins")
        performance_form.addRow("", self.plugins_checkbox)
        self.startup_checkbox = QCheckBox("Iniciar com o Windows")
        performance_form.addRow("", self.startup_checkbox)
        self.power_status_label = QLabel()
        performance_form.addRow("Energia", self.power_status_label)
        self.performance_status_label = QLabel("Compositor parado.")
        performance_form.addRow("Diagnóstico ao vivo", self.performance_status_label)
        self.hotkeys_checkbox = QCheckBox("Ativar atalhos globais: Ctrl+Alt+P, Ctrl+Alt+N e Ctrl+Alt+R")
        performance_form.addRow("", self.hotkeys_checkbox)
        self.telemetry_checkbox = QCheckBox("Enviar telemetria opcional quando um servidor for configurado")
        performance_form.addRow("", self.telemetry_checkbox)

        automation_layout = QVBoxLayout(automation_tab)
        automation_layout.addWidget(QLabel("Recursos automáticos e ferramentas de criação."))
        self.playlists_button = QPushButton("Gerenciar playlists")
        self.app_rules_button = QPushButton("Regras por aplicativo")
        self.scene_editor_button = QPushButton("Editor de cenas por camadas")
        self.catalog_button = QPushButton("Catálogo online")
        self.screensaver_button = QPushButton("Ativar como protetor de tela")
        for button in (
            self.playlists_button,
            self.app_rules_button,
            self.scene_editor_button,
            self.catalog_button,
            self.screensaver_button,
        ):
            automation_layout.addWidget(button)
        automation_layout.addStretch(1)

        support_layout = QVBoxLayout(support_tab)
        self.logs_button = QPushButton("Abrir logs")
        self.folder_button = QPushButton("Abrir pasta da biblioteca")
        self.support_button = QPushButton("Exportar diagnóstico")
        self.native_diag_button = QPushButton("Diagnóstico nativo")
        self.benchmark_button = QPushButton("Executar benchmark de 30 segundos")
        self.update_url_edit = QLineEdit()
        self.update_url_edit.setPlaceholderText("https://seu-site/movaura-update.json")
        self.update_button = QPushButton("Verificar atualizações")
        self.download_update_button = QPushButton("Baixar atualização verificada")
        self.download_update_button.setEnabled(False)
        self.quit_button = QPushButton("Sair do Movaura")
        for button in (
            self.logs_button,
            self.folder_button,
            self.support_button,
            self.native_diag_button,
            self.benchmark_button,
        ):
            support_layout.addWidget(button)
        support_layout.addWidget(QLabel("Servidor de atualizações"))
        support_layout.addWidget(self.update_url_edit)
        support_layout.addWidget(self.update_button)
        support_layout.addWidget(self.download_update_button)
        support_layout.addWidget(self.quit_button)
        support_layout.addStretch(1)

        self.status_label = QLabel("Pronto.")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)
        author_label = QLabel(APP_AUTHOR_SIGNATURE)
        author_label.setStyleSheet("color: #777; font-size: 11px;")
        root.addWidget(author_label)

        self._refresh_monitors()
        self.experience_combo.currentTextChanged.connect(self._mode_changed)
        self.renderer_combo.currentTextChanged.connect(self._update_contextual_controls)
        self.performance_combo.currentTextChanged.connect(self._performance_changed)
        self.browse_button.clicked.connect(self._browse_media)
        self.gallery_button.clicked.connect(self._open_library)
        self.monitor_profiles_button.clicked.connect(self._open_monitor_profiles)
        self.color_button.clicked.connect(self._pick_color)
        self.apply_button.clicked.connect(self._apply_settings)
        self.start_button.clicked.connect(self._start_wallpaper)
        self.stop_button.clicked.connect(self._stop_wallpaper)
        self.restore_button.clicked.connect(self._restore_wallpaper)
        self.logs_button.clicked.connect(self._open_logs)
        self.folder_button.clicked.connect(self._open_library_folder)
        self.support_button.clicked.connect(self._export_support_report)
        self.native_diag_button.clicked.connect(self._native_diagnose)
        self.benchmark_button.clicked.connect(self._run_benchmark)
        self.update_button.clicked.connect(self._check_updates)
        self.download_update_button.clicked.connect(self._download_update)
        self.quit_button.clicked.connect(self._quit)
        self.startup_checkbox.toggled.connect(self._startup_toggled)
        self.playlists_button.clicked.connect(self._open_playlists)
        self.app_rules_button.clicked.connect(self._open_app_rules)
        self.scene_editor_button.clicked.connect(self._open_scene_editor)
        self.quick_library_button.clicked.connect(self._open_library)
        self.quick_create_button.clicked.connect(self._open_quick_create)
        self.quick_preview_button.clicked.connect(self._preview_wallpaper)
        self.quick_stop_preview_button.clicked.connect(self._stop_preview)
        self.quick_start_button.clicked.connect(self._start_wallpaper)
        self.quick_optimize_button.clicked.connect(self._auto_fix_performance)
        self.quick_catalog_button.clicked.connect(self._open_catalog)
        self.quick_benchmark_button.clicked.connect(self._run_benchmark)
        self.quick_advanced_button.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        self.quick_pause_button.clicked.connect(self._toggle_pause)
        self.quick_stop_button.clicked.connect(self._stop_wallpaper)
        self.ai_generation_page.wallpaper_selected.connect(self._select_wallpaper)
        self.ai_generation_page.preview_requested.connect(self._preview_wallpaper)
        self.ai_generation_page.start_requested.connect(self._start_wallpaper)
        self.ai_generation_page.stop_requested.connect(self._stop_or_restore_wallpaper)
        self.ai_generation_page.library_requested.connect(self._open_library)
        self.ai_generation_page.status_changed.connect(self.status_label.setText)
        self.screen_combo.currentTextChanged.connect(self._refresh_quick_summary)
        self.quick_screen_combo.currentIndexChanged.connect(self._quick_screen_changed)
        self.catalog_button.clicked.connect(self._open_catalog)
        self.screensaver_button.clicked.connect(self._install_screensaver)

    def _refresh_profiles(self) -> None:
        current = self.profile_combo.currentData() or self.settings.get_str("selected_profile")
        self.profile_combo.clear()
        for profile in self.profile_manager.list_profiles():
            self.profile_combo.addItem(profile.name, profile.name)
        index = self.profile_combo.findData(current)
        self.profile_combo.setCurrentIndex(max(0, index))

    def _refresh_monitors(self) -> None:
        self.screen_combo.clear()
        self.quick_screen_combo.clear()
        self.screen_combo.addItem("Todos", "all")
        self.quick_screen_combo.addItem("Todos os monitores", "all")
        for monitor in self.monitor_manager.monitors():
            label = f"{monitor.index}: {monitor.name} ({monitor.width}x{monitor.height})"
            self.screen_combo.addItem(label, monitor.index)
            self.quick_screen_combo.addItem(label, monitor.index)

    def _load_settings_to_form(self) -> None:
        self._set_combo_value(self.experience_combo, EXPERIENCE_MODES, self.settings.get_str("experience_mode"))
        self._refresh_renderer_options(self.settings.get_str("renderer"))
        self._set_combo_value(self.wallpaper_position_combo, WALLPAPER_POSITIONS, self.settings.get_str("wallpaper_position"))
        self.media_path_edit.setText(self.settings.get_str("media_path"))
        self.color_edit.setText(self.settings.get_str("color"))
        self.fps_spin.setValue(self.settings.get_int("fps"))
        self._set_combo_value(
            self.multi_monitor_combo,
            MULTI_MONITOR_MODES,
            self.settings.get_str("multi_monitor_mode"),
        )
        self.tray_checkbox.setChecked(self.settings.get_bool("tray_enabled"))
        self.plugins_checkbox.setChecked(self.settings.get_bool("plugins_enabled"))
        self.pause_fullscreen_checkbox.setChecked(self.settings.get_bool("pause_when_fullscreen_app"))
        self.low_power_checkbox.setChecked(self.settings.get_bool("low_power_mode"))
        self.optimize_videos_checkbox.setChecked(self.settings.get_bool("optimize_videos"))
        self.auto_performance_checkbox.setChecked(self.settings.get_bool("auto_performance_enabled"))
        self.auto_cpu_spin.setValue(self.settings.get_int("auto_cpu_high_percent"))
        self.auto_memory_spin.setValue(self.settings.get_int("auto_memory_high_mb"))
        self.hotkeys_checkbox.setChecked(self.settings.get_bool("global_hotkeys_enabled"))
        self.telemetry_checkbox.setChecked(self.settings.get_bool("telemetry_enabled"))
        self.update_url_edit.setText(self.settings.get_str("update_manifest_url"))
        self.startup_checkbox.blockSignals(True)
        self.startup_checkbox.setChecked(self.startup_manager.is_enabled())
        self.startup_checkbox.blockSignals(False)
        profile_id = self.settings.get_str("performance_profile")
        label = next((name for name, data in PERFORMANCE_PROFILES.items() if data["id"] == profile_id), "Recomendado")
        self._set_combo_text(self.performance_combo, label)
        screen = self.settings.data.get("screen", "all")
        for index in range(self.screen_combo.count()):
            if self.screen_combo.itemData(index) == screen:
                self.screen_combo.setCurrentIndex(index)
                break
        for index in range(self.quick_screen_combo.count()):
            if self.quick_screen_combo.itemData(index) == screen:
                self.quick_screen_combo.setCurrentIndex(index)
                break
        self._update_contextual_controls()
        self._refresh_active_playlist_label()
        self._refresh_quick_summary()

    def _apply_form_to_settings(self) -> None:
        experience = EXPERIENCE_MODES[self.experience_combo.currentText()]
        self.settings.data.update(
            {
                "experience_mode": experience,
                "renderer": RENDERERS[self.renderer_combo.currentText()],
                "media_path": self.media_path_edit.text().strip(),
                "wallpaper_position": WALLPAPER_POSITIONS[self.wallpaper_position_combo.currentText()],
                "color": self.color_edit.text().strip() or "#0078ff",
                "fps": self.fps_spin.value(),
                "screen": self.screen_combo.currentData(),
                "multi_monitor_mode": MULTI_MONITOR_MODES[self.multi_monitor_combo.currentText()],
                "tray_enabled": self.tray_checkbox.isChecked(),
                "plugins_enabled": self.plugins_checkbox.isChecked(),
                "pause_when_fullscreen_app": self.pause_fullscreen_checkbox.isChecked(),
                "low_power_mode": self.low_power_checkbox.isChecked(),
                "optimize_videos": self.optimize_videos_checkbox.isChecked(),
                "auto_performance_enabled": self.auto_performance_checkbox.isChecked(),
                "auto_cpu_warning_percent": max(5, self.auto_cpu_spin.value() - 6),
                "auto_cpu_high_percent": self.auto_cpu_spin.value(),
                "auto_memory_high_mb": self.auto_memory_spin.value(),
                "performance_profile": PERFORMANCE_PROFILES[self.performance_combo.currentText()]["id"],
                "global_hotkeys_enabled": self.hotkeys_checkbox.isChecked(),
                "telemetry_enabled": self.telemetry_checkbox.isChecked(),
            }
        )
        if experience == "desktop-static":
            self.settings.data.update({"host_mode": "system-wallpaper", "native_surface": "preview"})
        elif experience == "animated-desktop":
            self.settings.data.update({"host_mode": "native-composition", "native_surface": "desktop-live"})
        elif experience == "animated-preview":
            self.settings.data.update({"host_mode": "native-composition", "native_surface": "preview"})
        else:
            self.settings.data.update({"host_mode": "native-composition", "native_surface": "fullscreen"})

    def _mode_changed(self) -> None:
        renderer = RENDERERS.get(self.renderer_combo.currentText(), "color")
        self._refresh_renderer_options(renderer)
        self._update_contextual_controls()

    def _refresh_renderer_options(self, preferred: str) -> None:
        compatible = MODE_RENDERERS[EXPERIENCE_MODES[self.experience_combo.currentText()]]
        self.renderer_combo.blockSignals(True)
        self.renderer_combo.clear()
        for label, renderer in RENDERERS.items():
            if renderer in compatible:
                self.renderer_combo.addItem(label)
        self._set_combo_value(self.renderer_combo, RENDERERS, preferred)
        self.renderer_combo.blockSignals(False)

    def _update_contextual_controls(self) -> None:
        renderer = RENDERERS.get(self.renderer_combo.currentText(), "color")
        static = EXPERIENCE_MODES[self.experience_combo.currentText()] == "desktop-static"
        uses_media = renderer in {"audio", "image", "video", "gif", "parallax"}
        self.media_path_edit.setEnabled(uses_media)
        self.browse_button.setEnabled(uses_media)
        self.wallpaper_position_combo.setEnabled(static and renderer == "image")
        self.screen_combo.setEnabled(not static)
        self.multi_monitor_combo.setEnabled(not static)
        self.color_edit.setEnabled(renderer in {"audio", "color", "opengl", "parallax", "sample_pulse"})
        self.color_button.setEnabled(self.color_edit.isEnabled())

    def _performance_changed(self) -> None:
        profile = PERFORMANCE_PROFILES[self.performance_combo.currentText()]
        self.fps_spin.setValue(profile["fps"])
        self.low_power_checkbox.setChecked(profile["low_power_mode"])
        self.optimize_videos_checkbox.setChecked(True)
        self.auto_performance_checkbox.setChecked(True)
        self.auto_cpu_spin.setValue(18)
        self.auto_memory_spin.setValue(260)
        self._refresh_quick_summary()

    def _apply_settings(self) -> None:
        self._apply_form_to_settings()
        self.settings.save()
        self.status_label.setText("Configurações salvas.")

    def _start_wallpaper(self) -> None:
        self.preview_launcher.stop()
        self._apply_form_to_settings()
        validation = self.validator.validate(self.settings.data)
        if not validation.success:
            QMessageBox.warning(self, "Não foi possível iniciar", validation.message)
            self.status_label.setText(validation.message)
            return
        self.settings.save()
        if (
            self.settings.get_str("experience_mode") != "desktop-static"
            and self.engine
            and self.engine.last_backend == PresentationBackend.NATIVE_COMPOSITION
        ):
            if self.engine.reconfigure_native_compositor():
                surface = self.settings.get_str("native_surface")
                self.status_label.setText(f"Compositor atualizado na {SURFACE_LABELS.get(surface, surface)}.")
                self._refresh_quick_summary()
            else:
                message = "Não foi possível atualizar a apresentação. Tente Parar e Iniciar novamente."
                self.status_label.setText(message)
                QMessageBox.warning(self, "Movaura", message)
            return
        self._stop_wallpaper(update_status=False)
        if self.settings.get_str("experience_mode") == "desktop-static":
            self._run_wallpaper_operation(
                "Aplicando papel de parede...",
                lambda: SystemWallpaperBackend().apply(
                    self.settings.get_str("renderer"),
                    self.settings.get_str("color"),
                    self.settings.get_str("media_path"),
                    self.settings.get_str("wallpaper_position"),
                ),
            )
            return
        self.engine = MovauraEngine(self.app, self.settings, diagnose=False, quit_when_no_windows=False)
        self.engine.set_control_panel(self)
        self.engine.set_status_callback(self.status_label.setText)
        self.engine.set_presentation_callback(self._sync_presentation_from_engine)
        self.engine.start()
        if self.engine.last_backend == PresentationBackend.NATIVE_COMPOSITION and self.engine.native_compositor.is_running:
            surface = self.settings.get_str("native_surface")
            self.status_label.setText(f"Compositor iniciado na {SURFACE_LABELS.get(surface, surface)}.")
        else:
            message = "Não foi possível iniciar o wallpaper. Exporte um diagnóstico na aba Suporte se o problema continuar."
            self.status_label.setText(message)
            QMessageBox.warning(self, "Movaura", message)
        self._refresh_quick_summary()

    def _stop_wallpaper(self, update_status: bool = True) -> None:
        self.preview_launcher.stop()
        if self.engine:
            self.engine.stop()
            self.engine = None
        if update_status:
            self.status_label.setText("Apresentação interrompida.")
        self._refresh_quick_summary()

    def _stop_or_restore_wallpaper(self) -> None:
        if self.settings.get_str("experience_mode") == "desktop-static":
            self._restore_wallpaper()
            return
        self._stop_wallpaper()

    def _toggle_pause(self) -> None:
        if not self.engine:
            self.status_label.setText("Nenhum wallpaper animado está ativo.")
            return
        self.engine.toggle_pause()
        self._refresh_quick_summary()

    def _preview_wallpaper(self) -> None:
        self._apply_form_to_settings()
        preview = dict(self.settings.data)
        preview["experience_mode"] = "animated-preview"
        validation = self.validator.validate(preview)
        if not validation.success:
            QMessageBox.warning(self, "Pré-visualização", validation.message)
            return
        result = self.preview_launcher.launch_renderer(
            renderer=self.settings.get_str("renderer"),
            color=self.settings.get_str("color"),
            fps=min(self.settings.get_int("fps"), 60),
            media_path=self.settings.get_str("media_path"),
            instance_key="control-panel-preview",
            effect_intensity=self.settings.get_int("effect_intensity"),
            effect_speed=self.settings.get_int("effect_speed"),
        )
        self.status_label.setText(result.message)
        if not result.success:
            QMessageBox.warning(self, "Pré-visualização", result.message)

    def _stop_preview(self) -> None:
        self.preview_launcher.stop()
        self.status_label.setText("Pré-visualização fechada.")

    def _quick_screen_changed(self) -> None:
        selected = self.quick_screen_combo.currentData()
        for index in range(self.screen_combo.count()):
            if self.screen_combo.itemData(index) == selected:
                self.screen_combo.setCurrentIndex(index)
                break
        self._refresh_quick_summary()

    def _auto_fix_performance(self) -> None:
        self._set_combo_text(self.performance_combo, "Leve")
        self.fps_spin.setValue(15)
        self.low_power_checkbox.setChecked(True)
        self.optimize_videos_checkbox.setChecked(True)
        self.pause_fullscreen_checkbox.setChecked(True)
        self._apply_form_to_settings()
        self.settings.save()
        if self.engine and self.engine.native_compositor.is_running:
            self.engine.reconfigure_native_compositor()
        self.status_label.setText("Desempenho corrigido: perfil Leve, 15 FPS e otimização de vídeos ativados.")
        self._refresh_quick_summary()

    def _restore_wallpaper(self) -> None:
        self._stop_wallpaper(update_status=False)
        self._run_wallpaper_operation("Restaurando papel de parede anterior...", lambda: SystemWallpaperBackend().restore())

    def _run_wallpaper_operation(self, status: str, operation: Callable[[], object]) -> None:
        if self.wallpaper_operation:
            return
        self.status_label.setText(status)
        self.start_button.setEnabled(False)
        self.restore_button.setEnabled(False)
        self.wallpaper_operation = BackgroundOperation()
        self.wallpaper_operation.finished.connect(self._wallpaper_finished)

        def run() -> None:
            try:
                result = operation()
            except Exception as exc:
                result = f"{type(exc).__name__}: {exc}"
            if self.wallpaper_operation:
                self.wallpaper_operation.finished.emit(result)

        Thread(target=run, daemon=True).start()

    def _wallpaper_finished(self, result: object) -> None:
        self.wallpaper_operation = None
        self.start_button.setEnabled(True)
        self.restore_button.setEnabled(True)
        self.status_label.setText(getattr(result, "message", str(result)))

    def _open_library(self, initial_path: object = None) -> None:
        path = initial_path if isinstance(initial_path, Path) else None
        dialog = LibraryDialog(self.library, self, initial_path=path)
        dialog.selected.connect(self._use_library_wallpaper)
        dialog.preview_requested.connect(self._preview_library_item)
        dialog.exec()

    def _use_library_wallpaper(self, wallpaper: WallpaperItem) -> None:
        self._select_wallpaper(wallpaper)
        self._start_wallpaper()

    def _preview_library_item(self, wallpaper: WallpaperItem) -> None:
        self._select_wallpaper(wallpaper)
        self._preview_wallpaper()

    def _open_monitor_profiles(self) -> None:
        dialog = MonitorProfilesDialog(self.settings, self.library, self)
        dialog.applied.connect(self._apply_monitor_assignments)
        dialog.exec()

    def _apply_monitor_assignments(self, assignments: dict) -> None:
        self.settings.data["monitor_assignments"] = assignments
        self.settings.save()
        if assignments:
            self.status_label.setText("Wallpapers independentes por tela configurados. Clique em Iniciar.")
        else:
            self.status_label.setText("Configuração por tela removida. O wallpaper global será utilizado.")

    def _open_playlists(self) -> None:
        dialog = PlaylistDialog(self.playlists, self.settings, self)
        dialog.saved.connect(self._sync_playlist_to_wallpaper_tab)
        dialog.exec()
        self._refresh_active_playlist_label()
        self.status_label.setText("Playlist sincronizada com a aba Wallpaper.")

    def _sync_playlist_to_wallpaper_tab(self, presentation: dict) -> None:
        if presentation:
            self.settings.data.update(presentation)
            self.settings.save()
        self._load_settings_to_form()
        self.status_label.setText("Playlist sincronizada com a aba Wallpaper. Clique em Iniciar para aplicar.")

    def _sync_presentation_from_engine(self, presentation: dict[str, object]) -> None:
        self.settings.data.update(presentation)
        self._load_settings_to_form()
        self.status_label.setText("A aba Wallpaper foi atualizada com o item atual da playlist.")

    def _refresh_active_playlist_label(self) -> None:
        if self.settings.get_bool("playlist_enabled"):
            self.active_playlist_label.setText(self.settings.get_str("active_playlist"))
        else:
            self.active_playlist_label.setText("desativada")

    def _open_app_rules(self) -> None:
        AppRulesDialog(self.app_rules, self.settings, self).exec()
        self.status_label.setText("Regras por aplicativo atualizadas. Reinicie a apresentação para aplicar.")

    def _open_scene_editor(self) -> None:
        dialog = SceneEditorDialog(self.settings, self)
        dialog.applied.connect(self._apply_scene)
        dialog.preview_requested.connect(self._preview_scene)
        dialog.exec()

    def _open_quick_create(self) -> None:
        dialog = QuickCreateDialog(self.settings, self)
        dialog.applied.connect(self._apply_scene)
        dialog.exec()

    def _apply_scene(self, data: dict) -> None:
        self.settings.data.update(data)
        self.settings.save()
        self._load_settings_to_form()
        self.status_label.setText("Cena criada. Clique em Iniciar para aplicar na área de trabalho.")
        self._refresh_quick_summary()

    def _preview_scene(self, data: dict) -> None:
        self.settings.data.update(data)
        self._load_settings_to_form()
        self._preview_wallpaper()

    def _open_catalog(self) -> None:
        dialog = CatalogDialog(self.catalog, self.library, self.settings, self)
        dialog.selected.connect(self._select_wallpaper)
        dialog.exec()

    def _install_screensaver(self) -> None:
        result = self.screensaver.install()
        self.status_label.setText(result.message)
        QMessageBox.information(self, "Protetor de tela", result.message)

    def _select_wallpaper(self, wallpaper: WallpaperItem) -> None:
        self.library.mark_recent(wallpaper)
        experience = "desktop-static" if wallpaper.kind == "image" else "animated-desktop"
        self._set_combo_value(self.experience_combo, EXPERIENCE_MODES, experience)
        self._mode_changed()
        self._set_combo_value(self.renderer_combo, RENDERERS, wallpaper.kind)
        self.media_path_edit.setText(str(wallpaper.path))
        self._update_contextual_controls()
        analysis = analyze_media(wallpaper.path)
        self.status_label.setText(f"Selecionado: {wallpaper.name}. {analysis.message} Clique em Iniciar.")
        self._refresh_quick_summary()

    def _browse_media(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Importar wallpapers",
            str(Path.home()),
            "Wallpapers (*.mp4 *.webm *.gif *.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not paths:
            return
        imported = self.library.import_files([Path(path) for path in paths])
        if imported:
            self._select_wallpaper(imported[0])
            analysis = analyze_media(imported[0].path)
            self.status_label.setText(
                f"{len(imported)} arquivo(s) importado(s). Primeiro arquivo: {analysis.user_summary}. {analysis.message}"
            )

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.color_edit.setText(color.name())

    def _load_selected_profile(self) -> None:
        profile = self.profile_manager.load(self.profile_combo.currentData() or "")
        if profile:
            self.settings.data.update(profile.data)
            self.settings.data["selected_profile"] = profile.name
            self.settings.save()
            self._load_settings_to_form()
            self.status_label.setText(f"Perfil carregado: {profile.name}.")

    def _save_current_profile(self) -> None:
        name = self.profile_combo.currentData() or "default"
        if self.profile_manager.is_default(name):
            self.status_label.setText("Crie um perfil pessoal antes de salvar alterações.")
            return
        self._apply_form_to_settings()
        self.profile_manager.save(name, self.settings)
        self.status_label.setText(f"Perfil salvo: {name}.")

    def _new_profile(self) -> None:
        name, accepted = QInputDialog.getText(self, "Novo perfil", "Nome do perfil")
        if accepted and name.strip() and not self.profile_manager.is_default(name):
            self._apply_form_to_settings()
            profile = self.profile_manager.save(name, self.settings)
            self.settings.data["selected_profile"] = profile.name
            self.settings.save()
            self._refresh_profiles()
            self.status_label.setText(f"Perfil criado: {profile.name}.")

    def _delete_selected_profile(self) -> None:
        name = self.profile_combo.currentData() or ""
        if self.profile_manager.is_default(name):
            self.status_label.setText("Os perfis padrão não podem ser excluídos.")
        elif self.profile_manager.delete(name):
            self._refresh_profiles()
            self.status_label.setText(f"Perfil excluído: {name}.")

    def _startup_toggled(self, enabled: bool) -> None:
        result = self.startup_manager.set_enabled(enabled)
        self.status_label.setText(result.message)

    def _refresh_power_status(self) -> None:
        status = self.power_status.read().on_battery
        self.power_status_label.setText("bateria" if status is True else "tomada" if status is False else "desconhecido")

    def _refresh_performance_status(self) -> None:
        if not self.engine or not self.engine.native_compositor.is_running:
            self.performance_status_label.setText("Compositor parado.")
            self._refresh_quick_summary()
            return
        self.performance_status_label.setText(
            self.engine.last_performance_snapshot.detailed_text()
            + (
                f" | limite adaptativo {self.engine._adaptive_fps_cap} FPS"
                if self.engine._adaptive_fps_cap
                else ""
            )
        )
        self._refresh_quick_summary()

    def _refresh_quick_summary(self) -> None:
        renderer = RENDERERS.get(self.renderer_combo.currentText(), "color") if self.renderer_combo.count() else "color"
        media = Path(self.media_path_edit.text()).name if self.media_path_edit.text().strip() else ""
        self.quick_wallpaper_label.setText(media or next((label for label, value in RENDERERS.items() if value == renderer), renderer))
        screen = self.screen_combo.currentData()
        self.quick_screen_combo.blockSignals(True)
        for index in range(self.quick_screen_combo.count()):
            if self.quick_screen_combo.itemData(index) == screen:
                self.quick_screen_combo.setCurrentIndex(index)
                break
        self.quick_screen_combo.blockSignals(False)
        advice = self.performance_advisor.advice(
            self.engine.last_performance_snapshot if self.engine else self.performance_status_label_to_snapshot(),
            renderer,
            self.fps_spin.value(),
            self.optimize_videos_checkbox.isChecked(),
        )
        self.quick_recommendation_label.setText(f"{advice.title}: {advice.message}")
        self.quick_setup_label.setText(
            self.performance_advisor.beginner_summary(
                renderer,
                media,
                screen,
                self.performance_combo.currentText() or "Recomendado",
            )
        )
        self.quick_optimize_button.setEnabled(advice.level in {"high", "warning", "idle"})
        if self.engine and self.engine.native_compositor.is_running:
            performance = self.engine.last_performance_snapshot.to_text()
            if self.engine._adaptive_fps_cap:
                performance += f" | limite {self.engine._adaptive_fps_cap} FPS"
            self.quick_performance_label.setText(performance)
            self.quick_state_label.setText("Pausado" if self.engine._native_paused else "Ativo")
        else:
            self.quick_performance_label.setText("Compositor parado")
            self.quick_state_label.setText("Parado")

    @staticmethod
    def performance_status_label_to_snapshot():
        return PerformanceSnapshot()

    def _open_logs(self) -> None:
        self._open_folder(log_path().parent)

    def _open_library_folder(self) -> None:
        self._open_folder(app_root() / "wallpapers")

    def _open_folder(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(path)
        except OSError as exc:
            self.status_label.setText(f"Não foi possível abrir a pasta: {exc}")

    def _native_diagnose(self) -> None:
        from core.native_host import NativeHost
        QMessageBox.information(self, "Diagnóstico nativo", NativeHost().probe_text())

    def _run_benchmark(self) -> None:
        if self.benchmark_operation:
            return
        if not self.engine or not self.engine.native_compositor.is_running:
            QMessageBox.information(self, "Benchmark", "Inicie um wallpaper animado antes de executar o benchmark.")
            return
        self.benchmark_button.setEnabled(False)
        self.status_label.setText("Medindo CPU e memoria por 30 segundos...")
        self.benchmark_operation = BackgroundOperation()
        self.benchmark_operation.finished.connect(self._benchmark_finished)
        process_ids = set(self.engine.native_compositor.process_ids)

        def run() -> None:
            result = run_benchmark(process_ids)
            if self.benchmark_operation:
                self.benchmark_operation.finished.emit(result)

        Thread(target=run, daemon=True).start()

    def _benchmark_finished(self, result: BenchmarkResult) -> None:
        self.benchmark_operation = None
        self.benchmark_button.setEnabled(True)
        self.settings.data["last_benchmark"] = result.to_text()
        self.settings.save()
        self.status_label.setText("Benchmark concluido.")
        message = result.to_text()
        if result.profile == "economy":
            answer = QMessageBox.question(
                self,
                "Benchmark concluido",
                f"{message}\n\nO Movaura recomenda o perfil Leve para este wallpaper. Aplicar agora?",
            )
            if answer == QMessageBox.StandardButton.Yes:
                self._auto_fix_performance()
            return
        QMessageBox.information(self, "Benchmark concluido", message)

    def _export_support_report(self) -> None:
        if self.support_operation:
            return
        self.support_button.setEnabled(False)
        self.status_label.setText("Exportando diagnóstico...")
        self.support_operation = BackgroundOperation()
        self.support_operation.finished.connect(self._support_finished)

        def run() -> None:
            try:
                result: object = create_support_report(self.settings)
            except Exception as exc:
                result = exc
            if self.support_operation:
                self.support_operation.finished.emit(result)

        Thread(target=run, daemon=True).start()

    def _support_finished(self, result: object) -> None:
        self.support_operation = None
        self.support_button.setEnabled(True)
        if isinstance(result, Path):
            self._open_folder(result.parent)
            self.status_label.setText(f"Diagnóstico exportado: {result.name}.")
        else:
            self.status_label.setText(f"Falha ao exportar diagnóstico: {result}")

    def _check_updates(self) -> None:
        if self.update_operation:
            return
        self.update_button.setEnabled(False)
        self.status_label.setText("Consultando atualizações...")
        self.update_operation = BackgroundOperation()
        self.update_operation.finished.connect(self._update_finished)
        manifest_url = self.update_url_edit.text().strip()
        self.settings.data["update_manifest_url"] = manifest_url
        self.settings.save()

        def run() -> None:
            result = self.update_checker.check(manifest_url)
            if self.update_operation:
                self.update_operation.finished.emit(result)

        Thread(target=run, daemon=True).start()

    def _update_finished(self, result: UpdateResult) -> None:
        self.update_operation = None
        self.update_button.setEnabled(True)
        self.status_label.setText(result.message)
        self.pending_update = result if result.available else None
        self.download_update_button.setEnabled(result.available)
        if not result.available:
            QMessageBox.information(self, "Atualizações", result.message)
            return
        answer = QMessageBox.question(self, "Atualização disponível", f"{result.message}\n\nBaixar agora com verificação SHA-256?")
        if answer == QMessageBox.StandardButton.Yes:
            self._download_update()

    def _download_update(self) -> None:
        if self.update_operation or not self.pending_update:
            return
        self.download_update_button.setEnabled(False)
        self.status_label.setText("Baixando atualização...")
        self.update_operation = BackgroundOperation()
        self.update_operation.finished.connect(self._download_update_finished)
        update = self.pending_update

        def run() -> None:
            try:
                result: object = self.update_checker.download(update)
            except Exception as exc:
                result = exc
            if self.update_operation:
                self.update_operation.finished.emit(result)

        Thread(target=run, daemon=True).start()

    def _download_update_finished(self, result: object) -> None:
        self.update_operation = None
        self.download_update_button.setEnabled(bool(self.pending_update))
        if isinstance(result, Path):
            self.status_label.setText(f"Atualização baixada e verificada: {result.name}.")
            self._open_folder(result.parent)
            return
        self.status_label.setText(f"Falha ao baixar atualização: {result}")

    def _quit(self) -> None:
        self._stop_wallpaper()
        self.settings.save()
        self.app.quit()

    def closeEvent(self, event) -> None:
        self.preview_launcher.stop()
        if self.engine and self.engine.tray and self.engine.tray.tray.isVisible():
            self.hide()
            self.engine.tray.notify_running_in_background()
            event.ignore()
            return
        self.settings.save()
        self.app.quit()
        super().closeEvent(event)

    @staticmethod
    def _set_combo_text(combo: QComboBox, text: str) -> None:
        index = combo.findText(text)
        combo.setCurrentIndex(max(0, index))

    def _set_combo_value(self, combo: QComboBox, values: dict[str, str], value: str) -> None:
        label = next((label for label, current in values.items() if current == value), "")
        self._set_combo_text(combo, label)
