"""
ARIA Settings Dialog — Swiss Modernism 2.0 Edition.
High-precision configuration matrix for AI providers, global shortcuts,
safety protocols, local Whisper speech engines, episodic memory, and systemd units.
"""

import os
import re
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QLineEdit, QComboBox, QSpinBox,
    QSlider, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon

from aria.config import config
from aria.gui.widgets import ToggleSwitch, SettingRow, StatusBadge, HotkeyPicker
from aria.gui.icons import get_icon, get_pixmap
from aria.agent.memory import Memory
from aria.utils.shortcuts import register_gnome_shortcut


class SettingsDialog(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ARIA // CONFIGURATION MATRIX")
        self.resize(800, 640)
        self.setObjectName("CentralWidget")

        self._load_styles()
        self._setup_ui()
        self._populate_current_settings()

    def _load_styles(self):
        qss_path = Path(__file__).parent / "styles.qss"
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text())

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(20)

        # ── Header ───────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(16)

        header_left = QVBoxLayout()
        header_left.setSpacing(3)

        tech_pre = QLabel("SYSTEM PARAMETERS // 00")
        tech_pre.setProperty("class", "tech-label")
        header_left.addWidget(tech_pre)

        title = QLabel("CONFIGURATION MATRIX")
        title.setProperty("class", "heading-2")
        header_left.addWidget(title)

        sub = QLabel("CALIBRATE REASONING MODELS, SHORTCUTS, HARDWARE INTERFACES & SAFETY GATES")
        sub.setProperty("class", "subtitle")
        header_left.addWidget(sub)

        header.addLayout(header_left)
        header.addStretch()

        badge_live = QLabel("[ MATRIX // ACTIVE ]")
        badge_live.setProperty("class", "badge-purple")
        header.addWidget(badge_live, alignment=Qt.AlignmentFlag.AlignTop)

        main_layout.addLayout(header)

        # ── Tab Widget with Professional Vector Icons ────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setIconSize(QSize(16, 16))
        self.tabs.addTab(self._create_providers_tab(), get_icon("cpu", color="#CED4E0", size=16), "01 // ENGINE")
        self.tabs.addTab(self._create_hotkey_hud_tab(), get_icon("keyboard", color="#CED4E0", size=16), "02 // INTERACTION")
        self.tabs.addTab(self._create_safety_tab(), get_icon("shield", color="#CED4E0", size=16), "03 // SECURITY")
        self.tabs.addTab(self._create_voice_tab(), get_icon("mic", color="#CED4E0", size=16), "04 // SPEECH")
        self.tabs.addTab(self._create_memory_tab(), get_icon("database", color="#CED4E0", size=16), "05 // MEMORY")
        self.tabs.addTab(self._create_system_tab(), get_icon("server", color="#CED4E0", size=16), "06 // SYSTEM")
        main_layout.addWidget(self.tabs, stretch=1)

        # ── Footer Buttons ───────────────────────────────────────────────────
        footer = QHBoxLayout()
        footer.setSpacing(12)

        self.btn_cancel = QPushButton("DISMISS / CANCEL")
        self.btn_cancel.setIcon(get_icon("cross", color="#CED4E0", size=13))
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("APPLY CONFIGURATION MATRIX ➔")
        self.btn_save.setIcon(get_icon("check", color="#090A0D", size=13))
        self.btn_save.setProperty("class", "primary-btn")
        self.btn_save.clicked.connect(self._save_settings)

        footer.addStretch()
        footer.addWidget(self.btn_cancel)
        footer.addWidget(self.btn_save)
        main_layout.addLayout(footer)

    # ── Tab 1: AI Providers ──────────────────────────────────────────────────
    def _create_providers_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(14)
        layout.setContentsMargins(16, 16, 16, 16)

        self.provider_select = QComboBox()
        self.provider_select.addItems(["gemini", "openai", "claude", "ollama"])
        self.provider_select.setFixedWidth(200)
        layout.addWidget(SettingRow(
            "REASONING INFERENCE PROVIDER",
            "Primary multimodal engine dispatched for planning, vision & computer use execution",
            self.provider_select
        ))

        self.input_gemini = QLineEdit()
        self.input_gemini.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_gemini.setPlaceholderText("AIzaSy...")
        layout.addWidget(SettingRow(
            "GOOGLE GEMINI API KEY",
            "Direct authentication token for Gemini 2.0 Flash / Pro multimodal APIs",
            self.input_gemini
        ))

        self.input_openai = QLineEdit()
        self.input_openai.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_openai.setPlaceholderText("sk-proj-...")
        layout.addWidget(SettingRow(
            "OPENAI PLATFORM KEY",
            "API bearer secret for GPT-4o & o1 visual reasoning inference",
            self.input_openai
        ))

        self.input_claude = QLineEdit()
        self.input_claude.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_claude.setPlaceholderText("sk-ant-...")
        layout.addWidget(SettingRow(
            "ANTHROPIC CLAUDE KEY",
            "API token for Claude 3.5 Sonnet computer-use agentic execution",
            self.input_claude
        ))

        self.input_ollama_url = QLineEdit()
        self.input_ollama_url.setPlaceholderText("http://127.0.0.1:11434")
        layout.addWidget(SettingRow(
            "LOCAL OLLAMA ENDPOINT",
            "Offline local LLM service address for air-gapped zero-cloud execution",
            self.input_ollama_url
        ))

        layout.addStretch()
        return w

    # ── Tab 2: Hotkey & HUD ──────────────────────────────────────────────────
    def _create_hotkey_hud_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(14)
        layout.setContentsMargins(16, 16, 16, 16)

        self.picker_hotkey = HotkeyPicker(config.hotkey)
        layout.addWidget(SettingRow(
            "GLOBAL SUMMON SHORTCUT",
            "System-wide key sequence intercepted by compositor to toggle floating HUD",
            self.picker_hotkey
        ))

        # HUD Width with telemetry label
        width_box = QWidget()
        w_layout = QHBoxLayout(width_box)
        w_layout.setContentsMargins(0, 0, 0, 0)
        w_layout.setSpacing(10)
        self.slider_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_width.setRange(520, 960)
        self.slider_width.setFixedWidth(160)
        self.lbl_width_metric = QLabel(f"{config.overlay_width}px")
        self.lbl_width_metric.setProperty("class", "tech-label")
        self.lbl_width_metric.setFixedWidth(50)
        self.slider_width.valueChanged.connect(lambda v: self.lbl_width_metric.setText(f"{v}px"))
        w_layout.addWidget(self.slider_width)
        w_layout.addWidget(self.lbl_width_metric)
        layout.addWidget(SettingRow(
            "HUD VIEWPORT WIDTH",
            "Horizontal geometric dimension of floating command interface (520px - 960px)",
            width_box
        ))

        # Opacity with telemetry label
        opac_box = QWidget()
        o_layout = QHBoxLayout(opac_box)
        o_layout.setContentsMargins(0, 0, 0, 0)
        o_layout.setSpacing(10)
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(70, 100)
        self.slider_opacity.setFixedWidth(160)
        self.lbl_opac_metric = QLabel(f"{int(config.overlay_opacity * 100)}%")
        self.lbl_opac_metric.setProperty("class", "tech-label")
        self.lbl_opac_metric.setFixedWidth(40)
        self.slider_opacity.valueChanged.connect(lambda v: self.lbl_opac_metric.setText(f"{v}%"))
        o_layout.addWidget(self.slider_opacity)
        o_layout.addWidget(self.lbl_opac_metric)
        layout.addWidget(SettingRow(
            "VIEWPORT GLASS OPACITY",
            "Translucency ratio of architectural floating HUD canvas (70% - 100%)",
            opac_box
        ))

        # Display server
        self.combo_display = QComboBox()
        self.combo_display.addItems(["wayland", "x11"])
        self.combo_display.setFixedWidth(160)
        layout.addWidget(SettingRow(
            "DISPLAY PROTOCOL",
            "Compositor pipeline: Wayland native (grim/ydotool) or X11 (pyautogui)",
            self.combo_display
        ))

        layout.addStretch()
        return w

    # ── Tab 3: Safety & Autonomy ─────────────────────────────────────────────
    def _create_safety_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(14)
        layout.setContentsMargins(16, 16, 16, 16)

        self.toggle_safe_mode = ToggleSwitch()
        layout.addWidget(SettingRow(
            "INTERCEPT DESTRUCTIVE ACTIONS",
            "Enforce stark modal barrier before deleting files, modifying code, or running bash scripts",
            self.toggle_safe_mode
        ))

        self.spin_max_steps = QSpinBox()
        self.spin_max_steps.setRange(1, 50)
        self.spin_max_steps.setFixedWidth(80)
        layout.addWidget(SettingRow(
            "MAX RECURSION STEPS",
            "Execution budget ceiling: maximum sequential tool actions permitted per user command",
            self.spin_max_steps
        ))

        layout.addStretch()
        return w

    # ── Tab 4: Voice & Audio ─────────────────────────────────────────────────
    def _create_voice_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(14)
        layout.setContentsMargins(16, 16, 16, 16)

        self.combo_whisper = QComboBox()
        self.combo_whisper.addItems(["tiny.en", "base.en", "small.en", "medium.en"])
        self.combo_whisper.setFixedWidth(160)
        layout.addWidget(SettingRow(
            "WHISPER INFERENCE MODEL",
            "Local neural speech model weights (base.en is fast; small.en maximizes precision)",
            self.combo_whisper
        ))

        self.input_voice_lang = QLineEdit()
        self.input_voice_lang.setFixedWidth(80)
        layout.addWidget(SettingRow(
            "SPEECH RECOGNITION LOCALE",
            "ISO 639-1 language code for speech transcription input (default: en)",
            self.input_voice_lang
        ))

        layout.addStretch()
        return w

    # ── Tab 5: Memory & Data ─────────────────────────────────────────────────
    def _create_memory_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(14)
        layout.setContentsMargins(16, 16, 16, 16)

        mem = Memory()
        hist = mem.get_recent_history(100)

        self.lbl_session_count = QLabel(f"SESSIONS LOGGED // {len(hist)}")
        self.lbl_session_count.setProperty("class", "badge-purple")
        layout.addWidget(SettingRow(
            "PERSISTENT EPISODIC SESSIONS",
            f"Stored in SQLite relational store at: {config.memory_dir}/memory.db",
            self.lbl_session_count
        ))

        btn_clear = QPushButton("PURGE EPISODIC MEMORY // RESET")
        btn_clear.setIcon(get_icon("trash", color="#FF3B30", size=13))
        btn_clear.setProperty("class", "danger-btn")
        btn_clear.clicked.connect(self._clear_memory)
        layout.addWidget(SettingRow(
            "PURGE CONTEXT MEMORY",
            "Permanently delete all stored task transcripts, command logs, and contextual summaries",
            btn_clear
        ))

        layout.addStretch()
        return w

    def _clear_memory(self):
        reply = QMessageBox.question(
            self, "RESET CONFIRMATION // MEMORY PURGE",
            "Are you sure you want to delete all past conversation history and episodic memory?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db_path = config.memory_dir / "memory.db"
            if db_path.exists():
                db_path.unlink()
            Memory()  # re-initialise empty tables
            self.lbl_session_count.setText("SESSIONS LOGGED // 0")
            QMessageBox.information(self, "MEMORY RESET", "Episodic memory tables cleared successfully.")

    # ── Tab 6: System & ARIA Service ─────────────────────────────────────────
    def _create_system_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(14)
        layout.setContentsMargins(16, 16, 16, 16)

        self.toggle_autostart = ToggleSwitch(checked=True)
        self.toggle_autostart.toggled.connect(self._toggle_systemd_service)
        layout.addWidget(SettingRow(
            "AUTOSTART ARIA ON LOGIN",
            "Register and enable systemd user unit 'aria.service' automatically upon desktop login",
            self.toggle_autostart
        ))

        btn_restart = QPushButton("RESTART ARIA // SIGTERM")
        btn_restart.setIcon(get_icon("refresh", color="#CED4E0", size=13))
        btn_restart.clicked.connect(self._restart_aria)
        layout.addWidget(SettingRow(
            "RELOAD ARIA CORE",
            "Restarts background aria.service to apply new environment configurations immediately",
            btn_restart
        ))

        layout.addStretch()
        return w

    def _toggle_systemd_service(self, enabled: bool):
        action = "enable" if enabled else "disable"
        subprocess.run(["systemctl", "--user", action, "aria.service"], capture_output=True)

    def _restart_aria(self):
        res = subprocess.run(["systemctl", "--user", "restart", "aria.service"], capture_output=True)
        if res.returncode == 0:
            QMessageBox.information(self, "ARIA RELOAD", "ARIA service restarted successfully.")
        else:
            QMessageBox.warning(self, "ARIA NOTICE", "Could not restart ARIA service (might be running manually).")

    _restart_daemon = _restart_aria

    # ── Load & Save ──────────────────────────────────────────────────────────
    def _populate_current_settings(self):
        # Providers
        idx = self.provider_select.findText(config.provider.lower())
        if idx >= 0:
            self.provider_select.setCurrentIndex(idx)
        self.input_gemini.setText(config.gemini_api_key)
        self.input_openai.setText(config.openai_api_key)
        self.input_claude.setText(config.anthropic_api_key)
        self.input_ollama_url.setText(config.ollama_base_url)

        # Hotkey & HUD
        self.picker_hotkey.setValue(config.hotkey)
        self.slider_width.setValue(config.overlay_width)
        self.lbl_width_metric.setText(f"{config.overlay_width}px")
        self.slider_opacity.setValue(int(config.overlay_opacity * 100))
        self.lbl_opac_metric.setText(f"{int(config.overlay_opacity * 100)}%")
        d_idx = self.combo_display.findText(config.display_server)
        if d_idx >= 0:
            self.combo_display.setCurrentIndex(d_idx)

        # Safety
        self.toggle_safe_mode.setChecked(config.confirm_destructive)
        self.spin_max_steps.setValue(config.max_steps)

        # Voice
        v_idx = self.combo_whisper.findText(config.voice_model)
        if v_idx >= 0:
            self.combo_whisper.setCurrentIndex(v_idx)
        self.input_voice_lang.setText(config.voice_language)

    def _save_settings(self):
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        content = env_path.read_text() if env_path.exists() else ""

        def update_kv(txt, k, v):
            pat = rf"^{k}=.*$"
            if re.search(pat, txt, flags=re.MULTILINE):
                return re.sub(pat, f"{k}={v}", txt, flags=re.MULTILINE)
            return txt + f"\n{k}={v}"

        content = update_kv(content, "ARIA_PROVIDER", self.provider_select.currentText())
        content = update_kv(content, "GEMINI_API_KEY", self.input_gemini.text().strip())
        content = update_kv(content, "OPENAI_API_KEY", self.input_openai.text().strip())
        content = update_kv(content, "ANTHROPIC_API_KEY", self.input_claude.text().strip())
        content = update_kv(content, "OLLAMA_BASE_URL", self.input_ollama_url.text().strip())

        hotkey_val = self.picker_hotkey.value()
        register_gnome_shortcut(hotkey_val)

        content = update_kv(content, "ARIA_HOTKEY", hotkey_val)
        content = update_kv(content, "ARIA_OVERLAY_WIDTH", str(self.slider_width.value()))
        content = update_kv(content, "ARIA_OVERLAY_OPACITY", f"{self.slider_opacity.value() / 100.0:.2f}")
        content = update_kv(content, "ARIA_DISPLAY_SERVER", self.combo_display.currentText())

        content = update_kv(content, "ARIA_CONFIRM_DESTRUCTIVE", "true" if self.toggle_safe_mode.isChecked() else "false")
        content = update_kv(content, "ARIA_MAX_STEPS", str(self.spin_max_steps.value()))

        content = update_kv(content, "ARIA_VOICE_MODEL", self.combo_whisper.currentText())
        content = update_kv(content, "ARIA_VOICE_LANGUAGE", self.input_voice_lang.text().strip())

        env_path.write_text(content)

        # Update in-memory config object
        config.provider = self.provider_select.currentText()
        config.gemini_api_key = self.input_gemini.text().strip()
        config.openai_api_key = self.input_openai.text().strip()
        config.anthropic_api_key = self.input_claude.text().strip()
        config.ollama_base_url = self.input_ollama_url.text().strip()
        config.hotkey = hotkey_val
        config.overlay_width = self.slider_width.value()
        config.overlay_opacity = self.slider_opacity.value() / 100.0
        config.display_server = self.combo_display.currentText()
        config.confirm_destructive = self.toggle_safe_mode.isChecked()
        config.max_steps = self.spin_max_steps.value()
        config.voice_model = self.combo_whisper.currentText()
        config.voice_language = self.input_voice_lang.text().strip()

        self.settings_saved.emit()
        QMessageBox.information(self, "CONFIGURATION SAVED", "Settings applied and synced to system environment.")
        self.accept()
