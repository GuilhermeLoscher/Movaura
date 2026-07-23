from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from core.app_rule_manager import AppRule, AppRuleManager
from core.catalog import CatalogItem, OnlineCatalog
from core.playlist_manager import PlaylistEntry, PlaylistManager
from core.monitor_manager import MonitorManager
from core.monitor_profile_manager import MonitorProfileManager
from core.scene_package import ScenePackageManager
from core.scene_layers import BLEND_MODES, normalize_layers, primary_background, primary_effect
from core.scene_presets import ScenePresetManager
from core.wallpaper_library import WallpaperLibrary


class PlaylistDialog(QDialog):
    saved = pyqtSignal(dict)

    def __init__(self, manager: PlaylistManager, settings, parent=None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.settings = settings
        self.entries: list[PlaylistEntry] = []
        self.setWindowTitle("Playlists")
        self.resize(700, 460)
        root = QVBoxLayout(self)
        top = QHBoxLayout()
        self.combo = QComboBox()
        self.enabled = QCheckBox("Ativar avanço automático")
        top.addWidget(QLabel("Playlist"))
        top.addWidget(self.combo, 1)
        top.addWidget(self.enabled)
        root.addLayout(top)
        self.list = QListWidget()
        root.addWidget(self.list, 1)
        buttons = QHBoxLayout()
        for label, callback in (
            ("Nova", self._new),
            ("Adicionar arquivos", self._add),
            ("Remover item", self._remove),
            ("Excluir playlist", self._delete),
            ("Salvar", self._save),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        root.addLayout(buttons)
        self.combo.currentTextChanged.connect(self._load)
        self._refresh_names()
        self.enabled.setChecked(settings.get_bool("playlist_enabled"))

    def _refresh_names(self, selected: str = "") -> None:
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(self.manager.names())
        index = self.combo.findText(selected or self.settings.get_str("active_playlist"))
        self.combo.setCurrentIndex(max(0, index))
        self.combo.blockSignals(False)
        self._load()

    def _load(self) -> None:
        self.entries = self.manager.entries(self.combo.currentText())
        self._render()

    def _render(self) -> None:
        self.list.clear()
        for entry in self.entries:
            self.list.addItem(f"{Path(entry.path).name}  |  {entry.duration_seconds}s")

    def _new(self) -> None:
        name, ok = QInputDialog.getText(self, "Nova playlist", "Nome")
        if ok and name.strip():
            self.manager.save(name.strip(), [])
            self._refresh_names(name.strip())

    def _add(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Adicionar à playlist", str(Path.home()), "Wallpapers (*.mp4 *.webm *.gif *.png *.jpg *.jpeg *.bmp *.webp)")
        if not paths:
            return
        duration, ok = QInputDialog.getInt(self, "Duração", "Segundos por wallpaper", 60, 5, 86400)
        if ok:
            self.entries.extend(PlaylistEntry(path, duration) for path in paths)
            self._render()

    def _remove(self) -> None:
        row = self.list.currentRow()
        if row >= 0:
            self.entries.pop(row)
            self._render()

    def _delete(self) -> None:
        if self.manager.delete(self.combo.currentText()):
            self._refresh_names("default")

    def _save(self) -> None:
        name = self.combo.currentText() or "default"
        self.manager.save(name, self.entries)
        self.settings.data["active_playlist"] = name
        self.settings.data["playlist_enabled"] = self.enabled.isChecked()
        presentation = self._first_valid_presentation()
        if presentation:
            self.settings.data.update(presentation)
        self.settings.save()
        self.saved.emit(presentation or {})
        self.accept()

    def _first_valid_presentation(self) -> dict:
        for entry in self.entries:
            presentation = self.manager.presentation_for(entry)
            if presentation:
                return presentation
        return {}


class AppRulesDialog(QDialog):
    def __init__(self, manager: AppRuleManager, settings, parent=None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.settings = settings
        self.rules = manager.rules()
        self.setWindowTitle("Regras por aplicativo")
        self.resize(560, 390)
        root = QVBoxLayout(self)
        self.enabled = QCheckBox("Ativar regras por aplicativo")
        self.enabled.setChecked(settings.get_bool("app_rules_enabled"))
        root.addWidget(self.enabled)
        root.addWidget(QLabel("O Movaura pausa enquanto um executável configurado estiver em primeiro plano."))
        self.list = QListWidget()
        root.addWidget(self.list, 1)
        buttons = QHBoxLayout()
        for label, callback in (("Adicionar", self._add), ("Remover", self._remove), ("Salvar", self._save)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        root.addLayout(buttons)
        self._render()

    def _render(self) -> None:
        self.list.clear()
        self.list.addItems(rule.executable for rule in self.rules)

    def _add(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar aplicativo", str(Path.home()), "Aplicativos (*.exe)")
        if path:
            executable = Path(path).name.lower()
            if executable not in {rule.executable for rule in self.rules}:
                self.rules.append(AppRule(executable))
                self._render()

    def _remove(self) -> None:
        row = self.list.currentRow()
        if row >= 0:
            self.rules.pop(row)
            self._render()

    def _save(self) -> None:
        self.manager.save(self.rules)
        self.settings.data["app_rules_enabled"] = self.enabled.isChecked()
        self.settings.save()
        self.accept()


class MonitorProfilesDialog(QDialog):
    applied = pyqtSignal(dict)

    def __init__(self, settings, library: WallpaperLibrary, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.library = library
        self.manager = MonitorProfileManager()
        self.rows: dict[str, QComboBox] = {}
        self.setWindowTitle("Wallpapers por monitor")
        self.resize(760, 360)
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Escolha um wallpaper diferente para cada tela ou deixe o padrão global."))
        form = QFormLayout()
        items = self.library.items()
        assignments = settings.data.get("monitor_assignments", {})
        for monitor in MonitorManager().monitors():
            combo = QComboBox()
            combo.addItem("Usar wallpaper global", "")
            for wallpaper in items:
                combo.addItem(f"{wallpaper.name} [{wallpaper.kind}]", str(wallpaper.path))
            selected = assignments.get(str(monitor.index), {}).get("media_path", "")
            combo.setCurrentIndex(max(0, combo.findData(selected)))
            form.addRow(f"{monitor.index}: {monitor.name}", combo)
            self.rows[str(monitor.index)] = combo
        root.addLayout(form)
        buttons = QHBoxLayout()
        clear = QPushButton("Limpar configurações por tela")
        save = QPushButton("Aplicar")
        cancel = QPushButton("Cancelar")
        clear.clicked.connect(self._clear)
        save.clicked.connect(self._apply)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(clear)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        root.addLayout(buttons)

    def _clear(self) -> None:
        for combo in self.rows.values():
            combo.setCurrentIndex(0)

    def _apply(self) -> None:
        assignments = {}
        for monitor, combo in self.rows.items():
            path = combo.currentData()
            if path:
                assignments[monitor] = self.manager.assignment_for_path(path)
        self.applied.emit(assignments)
        self.accept()


class QuickCreateDialog(QDialog):
    applied = pyqtSignal(dict)

    def __init__(self, settings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Criar wallpaper rapidamente")
        self.resize(560, 260)
        root = QVBoxLayout(self)
        form = QFormLayout()
        self.style = QComboBox()
        self.style.addItem("Usar mídia sem efeito", "media")
        self.style.addItem("Movimento sutil sobre a imagem", "parallax")
        self.style.addItem("Barras que reagem ao áudio", "audio")
        self.style.addItem("Pulso de cor animado", "opengl")
        self.background = QLineEdit(settings.get_str("media_path"))
        browse = QPushButton("Procurar")
        browse.clicked.connect(self._browse)
        background_row = QHBoxLayout()
        background_row.addWidget(self.background, 1)
        background_row.addWidget(browse)
        self.color = QLineEdit(settings.get_str("color"))
        choose_color = QPushButton("Escolher")
        choose_color.clicked.connect(self._pick)
        color_row = QHBoxLayout()
        color_row.addWidget(self.color, 1)
        color_row.addWidget(choose_color)
        self.quality = QComboBox()
        self.quality.addItem("Adaptativo recomendado", ("adaptive", 30))
        self.quality.addItem("Economia de recursos", ("economy", 15))
        self.quality.addItem("Qualidade máxima", ("quality", 60))
        form.addRow("Estilo", self.style)
        form.addRow("Wallpaper de fundo", background_row)
        form.addRow("Cor do efeito", color_row)
        form.addRow("Desempenho", self.quality)
        root.addLayout(form)
        create = QPushButton("Criar e deixar pronto para aplicar")
        create.clicked.connect(self._apply)
        root.addWidget(create)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar wallpaper",
            str(Path.home()),
            "Wallpapers (*.mp4 *.webm *.gif *.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if path:
            self.background.setText(path)

    def _pick(self) -> None:
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.color.setText(color.name())

    def _apply(self) -> None:
        style = str(self.style.currentData())
        media_path = self.background.text().strip()
        renderer = style
        if style == "media":
            renderer = self._renderer_for_path(media_path)
            if not renderer:
                QMessageBox.warning(self, "Criar wallpaper", "Escolha uma imagem, GIF ou vídeo.")
                return
        profile, fps = self.quality.currentData()
        effect_intensity = 25 if style == "parallax" else self.settings.get_int("effect_intensity")
        effect_speed = 70 if style == "parallax" else self.settings.get_int("effect_speed")
        self.applied.emit(
            {
                "experience_mode": "animated-desktop",
                "host_mode": "native-composition",
                "native_surface": "desktop-live",
                "renderer": renderer,
                "color": self.color.text().strip() or "#0078ff",
                "media_path": media_path,
                "fps": fps,
                "effect_intensity": effect_intensity,
                "effect_speed": effect_speed,
                "performance_profile": profile,
                "low_power_mode": profile != "quality",
            }
        )
        self.accept()

    @staticmethod
    def _renderer_for_path(path: str) -> str:
        suffix = Path(path).suffix.lower()
        if suffix in {".bmp", ".jpeg", ".jpg", ".png", ".webp"}:
            return "image"
        if suffix == ".gif":
            return "gif"
        if suffix in {".mp4", ".webm"}:
            return "video"
        return ""


class SceneEditorDialog(QDialog):
    applied = pyqtSignal(dict)
    preview_requested = pyqtSignal(dict)

    def __init__(self, settings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.packages = ScenePackageManager()
        self.presets = ScenePresetManager()
        self.layers = normalize_layers(
            settings.data.get("scene_layers"),
            settings.get_str("media_path"),
            settings.get_str("renderer"),
        )
        self.setWindowTitle("Editor de cenas por camadas")
        self.resize(760, 650)
        root = QVBoxLayout(self)
        preset_row = QHBoxLayout()
        self.preset = QComboBox()
        load_preset = QPushButton("Carregar preset")
        save_preset = QPushButton("Salvar preset")
        duplicate_preset = QPushButton("Duplicar preset")
        delete_preset = QPushButton("Excluir preset")
        load_preset.clicked.connect(self._load_preset)
        save_preset.clicked.connect(self._save_preset)
        duplicate_preset.clicked.connect(self._duplicate_preset)
        delete_preset.clicked.connect(self._delete_preset)
        preset_row.addWidget(QLabel("Preset"))
        preset_row.addWidget(self.preset, 1)
        for button in (load_preset, save_preset, duplicate_preset, delete_preset):
            preset_row.addWidget(button)
        root.addLayout(preset_row)
        self.layer_list = QListWidget()
        self.layer_list.setMinimumHeight(120)
        root.addWidget(self.layer_list)
        quick_row = QHBoxLayout()
        for label, callback in (
            ("Cena leve", lambda: self._apply_template("parallax")),
            ("Áudio", lambda: self._apply_template("audio")),
            ("Partículas", lambda: self._apply_template("particles")),
            ("Chuva", lambda: self._apply_template("rain")),
            ("Vídeo limpo", lambda: self._apply_template("media")),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            quick_row.addWidget(button)
        root.addLayout(quick_row)
        layer_buttons = QHBoxLayout()
        for label, callback in (
            ("Adicionar efeito", self._add_layer),
            ("Remover", self._remove_layer),
            ("Subir", lambda: self._move_layer(-1)),
            ("Descer", lambda: self._move_layer(1)),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            layer_buttons.addWidget(button)
        root.addLayout(layer_buttons)
        form = QFormLayout()
        self.effect = QComboBox()
        self.effect.addItem("Sem efeito: exibir somente o fundo", "media")
        self.effect.addItem("Pulso animado sobre cor", "opengl")
        self.effect.addItem("Parallax suave", "parallax")
        self.effect.addItem("Visualizador de áudio", "audio")
        self.effect.addItem("Particulas leves", "particles")
        self.effect.addItem("Chuva", "rain")
        self.effect.addItem("Neblina", "fog")
        self.effect.addItem("Brilho suave", "glow")
        self.effect.addItem("Vinheta", "vignette")
        self.color = QLineEdit(settings.get_str("color"))
        pick = QPushButton("Escolher")
        pick.clicked.connect(self._pick)
        color_row = QHBoxLayout()
        color_row.addWidget(self.color, 1)
        color_row.addWidget(pick)
        self.background = QLineEdit(settings.get_str("media_path"))
        background_button = QPushButton("Procurar")
        background_button.clicked.connect(self._browse_background)
        background_row = QHBoxLayout()
        background_row.addWidget(self.background, 1)
        background_row.addWidget(background_button)
        self.fps = QSpinBox()
        self.fps.setRange(1, 60)
        self.fps.setValue(settings.get_int("fps"))
        self.intensity = QSlider(Qt.Orientation.Horizontal)
        self.intensity.setRange(0, 100)
        self.intensity.setValue(settings.get_int("effect_intensity"))
        self.intensity.setToolTip("Controla a força visual do efeito selecionado.")
        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setRange(10, 200)
        self.speed.setValue(settings.get_int("effect_speed"))
        self.speed.setToolTip("Controla a velocidade do efeito. 100 representa a velocidade normal.")
        self.layer_enabled = QCheckBox("Camada visivel")
        self.layer_opacity = QSpinBox()
        self.layer_opacity.setRange(0, 100)
        self.layer_scale = QSpinBox()
        self.layer_scale.setRange(10, 300)
        self.layer_x = QSpinBox()
        self.layer_x.setRange(-100, 100)
        self.layer_y = QSpinBox()
        self.layer_y.setRange(-100, 100)
        self.layer_blend = QComboBox()
        self.layer_blend.addItems(BLEND_MODES)
        form.addRow("Camada 1: fundo", background_row)
        form.addRow("Camada 2: efeito", self.effect)
        form.addRow("Cor do efeito", color_row)
        form.addRow("Intensidade do efeito", self.intensity)
        form.addRow("Velocidade do efeito", self.speed)
        form.addRow("Fluidez máxima", self.fps)
        form.addRow("", self.layer_enabled)
        form.addRow("Opacidade da camada", self.layer_opacity)
        form.addRow("Escala da camada", self.layer_scale)
        form.addRow("Posicao X", self.layer_x)
        form.addRow("Posicao Y", self.layer_y)
        form.addRow("Mistura", self.layer_blend)
        root.addLayout(form)
        root.addWidget(QLabel("O visualizador usa o som do sistema. O parallax adiciona movimento suave à imagem."))
        buttons = QHBoxLayout()
        import_button = QPushButton("Importar pacote")
        export_button = QPushButton("Exportar pacote")
        preview_button = QPushButton("Pré-visualizar cena")
        apply_button = QPushButton("Usar esta cena")
        import_button.clicked.connect(self._import_package)
        export_button.clicked.connect(self._export_package)
        preview_button.clicked.connect(self._preview)
        apply_button.clicked.connect(self._apply)
        buttons.addWidget(import_button)
        buttons.addWidget(export_button)
        buttons.addWidget(preview_button)
        buttons.addStretch(1)
        buttons.addWidget(apply_button)
        root.addLayout(buttons)
        self.layer_list.currentRowChanged.connect(self._load_layer_controls)
        self.effect.currentIndexChanged.connect(self._update_selected_layer)
        self.layer_enabled.toggled.connect(self._update_selected_layer)
        self.layer_opacity.valueChanged.connect(self._update_selected_layer)
        self.layer_scale.valueChanged.connect(self._update_selected_layer)
        self.layer_x.valueChanged.connect(self._update_selected_layer)
        self.layer_y.valueChanged.connect(self._update_selected_layer)
        self.layer_blend.currentTextChanged.connect(self._update_selected_layer)
        self._refresh_presets()
        self._render_layers()

    def _pick(self) -> None:
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.color.setText(color.name())

    def _browse_background(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar wallpaper de fundo",
            str(Path.home()),
            "Wallpapers (*.mp4 *.webm *.gif *.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if path:
            self.background.setText(path)

    def _apply(self) -> None:
        data = self._scene_data()
        if not data:
            return
        self.applied.emit(data)
        self.accept()

    def _preview(self) -> None:
        data = self._scene_data()
        if data:
            self.preview_requested.emit(data)

    def _scene_data(self) -> dict:
        self._update_selected_layer()
        for layer in self.layers:
            if layer.get("kind") == "background":
                layer["media_path"] = self.background.text().strip()
                break
        background = primary_background(self.layers, self.background.text().strip())
        renderer = primary_effect(self.layers, str(self.effect.currentData()))
        if renderer == "media":
            renderer = QuickCreateDialog._renderer_for_path(background)
            if not renderer:
                QMessageBox.warning(self, "Editor de cenas", "Escolha uma imagem, GIF ou vídeo para a camada de fundo.")
                return {}
        return {
            "experience_mode": "animated-desktop",
            "host_mode": "native-composition",
            "native_surface": "desktop-live",
            "renderer": renderer,
            "color": self.color.text().strip() or "#0078ff",
            "media_path": background,
            "fps": self.fps.value(),
            "effect_intensity": self.intensity.value(),
            "effect_speed": self.speed.value(),
            "performance_profile": "economy" if self.fps.value() <= 15 else "adaptive",
            "low_power_mode": self.fps.value() <= 30,
            "optimize_videos": True,
            "scene_layers": list(self.layers),
        }

    def _render_layers(self, selected: int | None = None) -> None:
        row = self.layer_list.currentRow() if selected is None else selected
        self.layer_list.blockSignals(True)
        self.layer_list.clear()
        for layer in self.layers:
            visibility = "" if layer.get("enabled", True) else " [oculta]"
            self.layer_list.addItem(f"{layer.get('name', 'Camada')} | {layer.get('effect', 'media')}{visibility}")
        self.layer_list.setCurrentRow(max(0, min(row, len(self.layers) - 1)))
        self.layer_list.blockSignals(False)
        self._load_layer_controls(self.layer_list.currentRow())

    def _load_layer_controls(self, row: int) -> None:
        if row < 0 or row >= len(self.layers):
            return
        layer = self.layers[row]
        widgets = (self.effect, self.layer_enabled, self.layer_opacity, self.layer_scale, self.layer_x, self.layer_y, self.layer_blend)
        for widget in widgets:
            widget.blockSignals(True)
        index = self.effect.findData(str(layer.get("effect", "pulse")))
        self.effect.setCurrentIndex(max(0, index))
        self.layer_enabled.setChecked(bool(layer.get("enabled", True)))
        self.layer_opacity.setValue(int(layer.get("opacity", 100)))
        self.layer_scale.setValue(int(layer.get("scale", 100)))
        self.layer_x.setValue(int(layer.get("x", 0)))
        self.layer_y.setValue(int(layer.get("y", 0)))
        self.layer_blend.setCurrentText(str(layer.get("blend", "normal")))
        for widget in widgets:
            widget.blockSignals(False)

    def _update_selected_layer(self, *_args) -> None:
        row = self.layer_list.currentRow()
        if row < 0 or row >= len(self.layers):
            return
        layer = self.layers[row]
        if layer.get("kind") != "background":
            layer["effect"] = str(self.effect.currentData())
        layer.update(
            enabled=self.layer_enabled.isChecked(),
            opacity=self.layer_opacity.value(),
            scale=self.layer_scale.value(),
            x=self.layer_x.value(),
            y=self.layer_y.value(),
            blend=self.layer_blend.currentText(),
        )
        if layer.get("kind") == "background":
            layer["media_path"] = self.background.text().strip()

    def _add_layer(self) -> None:
        self.layers.append({"name": f"Efeito {len(self.layers)}", "kind": "effect", "effect": "pulse", "enabled": True, "opacity": 70, "x": 0, "y": 0, "scale": 100, "blend": "screen", "media_path": ""})
        self._render_layers(len(self.layers) - 1)

    def _apply_template(self, effect: str) -> None:
        background = self.background.text().strip()
        self.layers = [
            {
                "name": "Fundo",
                "kind": "background",
                "effect": "media",
                "enabled": True,
                "opacity": 100,
                "x": 0,
                "y": 0,
                "scale": 100,
                "blend": "normal",
                "media_path": background,
            }
        ]
        if effect != "media":
            self.layers.append(
                {
                    "name": "Efeito principal",
                    "kind": "effect",
                    "effect": effect,
                    "enabled": True,
                    "opacity": 72 if effect in {"particles", "rain"} else 85,
                    "x": 0,
                    "y": 0,
                    "scale": 100,
                    "blend": "screen",
                    "media_path": "",
                }
            )
        if effect == "parallax":
            self.fps.setValue(min(self.fps.value(), 30))
            self.intensity.setValue(25)
            self.speed.setValue(70)
        else:
            self.fps.setValue(15 if effect in {"particles", "rain"} else min(self.fps.value(), 30))
            self.intensity.setValue(60 if effect in {"particles", "rain"} else 70)
            self.speed.setValue(90 if effect == "rain" else 100)
        index = self.effect.findData(effect)
        self.effect.setCurrentIndex(max(0, index))
        self._render_layers(0)

    def _remove_layer(self) -> None:
        row = self.layer_list.currentRow()
        if row > 0:
            self.layers.pop(row)
            self._render_layers(row - 1)

    def _move_layer(self, offset: int) -> None:
        row = self.layer_list.currentRow()
        target = row + offset
        if row >= 0 and 0 <= target < len(self.layers):
            self.layers[row], self.layers[target] = self.layers[target], self.layers[row]
            self._render_layers(target)

    def _refresh_presets(self, selected: str = "") -> None:
        self.preset.clear()
        self.preset.addItems(self.presets.names())
        if selected:
            self.preset.setCurrentText(selected)

    def _save_preset(self) -> None:
        name, ok = QInputDialog.getText(self, "Salvar preset", "Nome")
        if ok and name.strip():
            self.presets.save(name, self._scene_data())
            self._refresh_presets(name.strip())

    def _load_preset(self) -> None:
        scene = self.presets.load(self.preset.currentText())
        if scene:
            self._restore_scene(scene)

    def _duplicate_preset(self) -> None:
        name, ok = QInputDialog.getText(self, "Duplicar preset", "Novo nome")
        if ok and name.strip() and self.presets.duplicate(self.preset.currentText(), name.strip()):
            self._refresh_presets(name.strip())

    def _delete_preset(self) -> None:
        if self.presets.delete(self.preset.currentText()):
            self._refresh_presets()

    def _restore_scene(self, settings: dict[str, object]) -> None:
        self.background.setText(str(settings.get("media_path", "")))
        self.color.setText(str(settings.get("color", "#0078ff")))
        self.fps.setValue(int(settings.get("fps", 30)))
        self.intensity.setValue(int(settings.get("effect_intensity", 70)))
        self.speed.setValue(int(settings.get("effect_speed", 100)))
        self.layers = normalize_layers(settings.get("scene_layers"), self.background.text(), str(settings.get("renderer", "parallax")))
        self._render_layers()

    def _export_package(self) -> None:
        data = self._scene_data()
        if not data:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Exportar pacote de cena", str(Path.home() / "minha-cena.movaura"), "Cenas Movaura (*.movaura)")
        if path:
            QMessageBox.information(self, "Pacote de cena", self.packages.export_scene(Path(path), data).message)

    def _import_package(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Importar pacote de cena", str(Path.home()), "Cenas Movaura (*.movaura)")
        if not path:
            return
        result = self.packages.import_scene(Path(path))
        if not result.success or not result.settings:
            QMessageBox.warning(self, "Pacote de cena", result.message)
            return
        settings = result.settings
        self._restore_scene(settings)
        renderer = str(settings.get("renderer", "color"))
        index = self.effect.findData(renderer)
        if index < 0 and renderer in {"gif", "image", "video"}:
            index = self.effect.findData("media")
        self.effect.setCurrentIndex(max(0, index))
        QMessageBox.information(self, "Pacote de cena", result.message)


class CatalogDialog(QDialog):
    selected = pyqtSignal(object)

    def __init__(self, catalog: OnlineCatalog, library: WallpaperLibrary, settings, parent=None) -> None:
        super().__init__(parent)
        self.catalog = catalog
        self.library = library
        self.settings = settings
        self.items: list[CatalogItem] = []
        self.setWindowTitle("Catálogo online")
        self.resize(700, 480)
        root = QVBoxLayout(self)
        url_row = QHBoxLayout()
        self.url = QLineEdit(settings.get_str("catalog_manifest_url"))
        self.url.setPlaceholderText("https://seu-site/catalogo.json")
        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self._refresh)
        url_row.addWidget(self.url, 1)
        url_row.addWidget(refresh)
        root.addLayout(url_row)
        self.list = QListWidget()
        root.addWidget(self.list, 1)
        download = QPushButton("Baixar para minha biblioteca")
        download.clicked.connect(self._download)
        root.addWidget(download)

    def _refresh(self) -> None:
        self.settings.data["catalog_manifest_url"] = self.url.text().strip()
        self.settings.save()
        try:
            self.items = self.catalog.fetch(self.url.text())
        except Exception as exc:
            QMessageBox.warning(self, "Catálogo", f"Não foi possível consultar o catálogo: {exc}")
            return
        self.list.clear()
        for item in self.items:
            row = QListWidgetItem(f"{item.name}\n{item.description}".strip())
            row.setData(256, item)
            self.list.addItem(row)

    def _download(self) -> None:
        row = self.list.currentItem()
        if not row:
            return
        try:
            downloaded = self.catalog.download(row.data(256))
            imported = self.library.import_files([downloaded])
        except Exception as exc:
            QMessageBox.warning(self, "Catálogo", f"Falha no download: {exc}")
            return
        QMessageBox.information(self, "Catálogo", "Wallpaper adicionado à biblioteca pessoal.")
        if imported:
            self.selected.emit(imported[0])
