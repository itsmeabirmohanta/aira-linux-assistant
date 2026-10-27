"""
ARIA Control Center & Dashboard — Swiss Modernism 2.0 Edition.
The primary desktop application window for controlling the resident agent,
summoning the HUD, viewing session history, running diagnostics, and accessing settings.
Fully integrated with professional vector SVG icons, mathematical padding, and high-precision telemetry.
"""

import os
import subprocess
import socket
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon

from aria.config import config
from aria.gui.widgets import StatusBadge, ActionCard
from aria.gui.icons import get_icon, get_pixmap
from aria.gui.settings_dialog import SettingsDialog
from aria.gui.onboarding import OnboardingWizard
from aria.agent.memory import Memory


class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARIA // CONTROL MATRIX")
        self.resize(920, 660)
        self.setMinimumSize(820, 580)
        self.setObjectName("CentralWidget")

        self.memory = Memory()
        self._load_styles()
        self._setup_ui()
        self._refresh_history()

        # Timer to poll ARIA core and socket status every 3 seconds
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._check_aria_status)
        self._poll_timer.start(3000)
        self._check_aria_status()

    def _load_styles(self):
        qss_path = Path(__file__).parent / "styles.qss"
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text())

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(32, 26, 32, 26)
        main_layout.setSpacing(20)

        # ── Top Bar (Swiss Modernism Header with Professional Icons) ─────────
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        # Logo mark + title
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(10)

        brand_icon = QLabel()
        brand_icon.setFixedSize(28, 28)
        brand_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_icon.setStyleSheet(
            "background-color: #0055FF; border: 1px solid #0055FF; border-radius: 4px;"
        )
        brand_icon.setPixmap(get_pixmap("sparkles", color="#FFFFFF", size=16))

        logo_label = QLabel("ARIA // 2.0  CONTROL MATRIX")
        logo_label.setProperty("class", "heading-1")

        brand_layout.addWidget(brand_icon)
        brand_layout.addWidget(logo_label)

        self.hotkey_pill = QLabel(f"[ TRIGGER: {config.hotkey.upper()} ]")
        self.hotkey_pill.setProperty("class", "badge-purple")

        btn_summon = QPushButton("SUMMON HUD ➔")
        btn_summon.setIcon(get_icon("play", color="#090A0D", size=13))
        btn_summon.setProperty("class", "primary-btn")
        btn_summon.setToolTip("Summon the floating command overlay (Ctrl+Space)")
        btn_summon.clicked.connect(self._summon_hud)

        btn_settings = QPushButton("SETTINGS")
        btn_settings.setIcon(get_icon("settings", color="#CED4E0", size=13))
        btn_settings.setToolTip("Open full system configuration matrix")
        btn_settings.clicked.connect(self._open_settings)

        btn_wizard = QPushButton("WALKTHROUGH")
        btn_wizard.setIcon(get_icon("compass", color="#CED4E0", size=13))
        btn_wizard.setProperty("class", "ghost-btn")
        btn_wizard.setToolTip("Launch interactive setup & feature walkthrough")
        btn_wizard.clicked.connect(self._open_onboarding)

        top_bar.addLayout(brand_layout)
        top_bar.addWidget(self.hotkey_pill)
        top_bar.addStretch()
        top_bar.addWidget(btn_summon)
        top_bar.addWidget(btn_settings)
        top_bar.addWidget(btn_wizard)
        main_layout.addLayout(top_bar)

        # ── Hero Status Banner (Swiss Telemetry Grid) ────────────────────────
        hero_banner = QFrame()
        hero_banner.setProperty("class", "highlight-card")
        hero_layout = QHBoxLayout(hero_banner)
        hero_layout.setContentsMargins(24, 18, 24, 18)
        hero_layout.setSpacing(24)

        status_info = QVBoxLayout()
        status_info.setSpacing(6)

        status_title_row = QHBoxLayout()
        status_heading = QLabel("SYSTEM STATUS //")
        status_heading.setProperty("class", "heading-3")
        self.status_badge = StatusBadge("Checking...", "purple")
        status_title_row.addWidget(status_heading)
        status_title_row.addWidget(self.status_badge)
        status_title_row.addStretch()

        self.info_label = QLabel(
            f"ENGINE: <b>{config.provider.upper()}</b>  •  "
            f"DISPLAY: <b>{config.display_server.upper()}</b>  •  "
            f"SECURITY: <b>{'PROTECTED' if config.confirm_destructive else 'AUTONOMOUS'}</b>  •  "
            f"CONTEXT_DEPTH: <b>{config.context_window}</b>"
        )
        self.info_label.setProperty("class", "subtitle")

        status_info.addLayout(status_title_row)
        status_info.addWidget(self.info_label)
        hero_layout.addLayout(status_info, stretch=1)

        # Control Buttons with Vector Icons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.btn_toggle_aria = QPushButton("START ARIA")
        self.btn_toggle_aria.setIcon(get_icon("power", color="#00E575", size=13))
        self.btn_toggle_aria.setProperty("class", "success-btn")
        self.btn_toggle_aria.clicked.connect(self._toggle_aria)

        self.btn_restart_aria = QPushButton("RELOAD ARIA")
        self.btn_restart_aria.setIcon(get_icon("refresh", color="#CED4E0", size=13))
        self.btn_restart_aria.clicked.connect(self._restart_aria)

        # Aliases for backward compatibility
        self.btn_toggle_daemon = self.btn_toggle_aria
        self.btn_restart_daemon = self.btn_restart_aria

        btn_layout.addWidget(self.btn_toggle_aria)
        btn_layout.addWidget(self.btn_restart_aria)
        hero_layout.addLayout(btn_layout)

        main_layout.addWidget(hero_banner)

        # ── Quick Action Cards (Modular Grid with Vector Icons) ───────────────
        actions_header = QLabel("COMMAND MODULES // QUICK INVOCATION")
        actions_header.setProperty("class", "heading-3")
        main_layout.addWidget(actions_header)

        actions_grid = QHBoxLayout()
        actions_grid.setSpacing(14)

        card1 = ActionCard("screen", "Screen Vision", "Visual inspection of active windows, errors, and layout.", index="01")
        card1.clicked.connect(lambda: self._quick_prompt("What is currently on my screen? Summarize what you see."))

        card2 = ActionCard("terminal", "Diagnostics", "Execute system telemetry: CPU, memory load, and disk allocation.", index="02")
        card2.clicked.connect(lambda: self._quick_prompt("Run a quick system diagnostic: check CPU, memory, and disk usage."))

        card3 = ActionCard("globe", "Web Engine", "Autonomous browser navigation, form interaction, content scraping.", index="03")
        card3.clicked.connect(lambda: self._quick_prompt("Open Chromium browser and search for latest Ubuntu Linux release notes."))

        card4 = ActionCard("mic", "Voice Pipeline", "100% offline local voice transcription pipeline via Whisper.", index="04")
        card4.clicked.connect(self._summon_hud)

        actions_grid.addWidget(card1)
        actions_grid.addWidget(card2)
        actions_grid.addWidget(card3)
        actions_grid.addWidget(card4)
        main_layout.addLayout(actions_grid)

        # ── Recent Tasks / History Section ───────────────────────────────────
        history_header_row = QHBoxLayout()
        history_title = QLabel("TASK TELEMETRY // MEMORY LOGS")
        history_title.setProperty("class", "heading-3")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("FILTER LOGS...")
        self.search_input.setFixedWidth(220)
        self.search_input.textChanged.connect(self._filter_history)

        btn_refresh = QPushButton("REFRESH")
        btn_refresh.setIcon(get_icon("refresh", color="#CED4E0", size=13))
        btn_refresh.setProperty("class", "ghost-btn")
        btn_refresh.clicked.connect(self._refresh_history)

        history_header_row.addWidget(history_title)
        history_header_row.addStretch()
        history_header_row.addWidget(self.search_input)
        history_header_row.addWidget(btn_refresh)
        main_layout.addLayout(history_header_row)

        self.table_history = QTableWidget()
        self.table_history.setColumnCount(3)
        self.table_history.setHorizontalHeaderLabels(["TIMESTAMP //", "TASK DIRECTIVE //", "EXECUTION SUMMARY //"])
        self.table_history.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_history.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_history.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_history.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_history.verticalHeader().setVisible(False)
        self.table_history.setShowGrid(False)
        self.table_history.setAlternatingRowColors(True)
        main_layout.addWidget(self.table_history, stretch=1)

    # ── ARIA Service Monitoring ──────────────────────────────────────────────
    def _is_aria_socket_alive(self) -> bool:
        sock_path = Path.home() / ".aria" / "aria.sock"
        if not sock_path.exists():
            return False
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(str(sock_path))
            s.close()
            return True
        except Exception:
            return False

    _is_daemon_socket_alive = _is_aria_socket_alive

    def _is_systemd_unit_active(self) -> bool:
        try:
            res = subprocess.run(
                ["systemctl", "--user", "is-active", "aria.service"],
                capture_output=True, text=True
            )
            return res.stdout.strip() == "active"
        except Exception:
            return False

    def _check_aria_status(self):
        socket_alive = self._is_aria_socket_alive()
        unit_active = self._is_systemd_unit_active()

        if socket_alive and unit_active:
            self.status_badge.set_status("ONLINE // ARMED", "green")
            self.btn_toggle_aria.setText("DISARM ARIA")
            self.btn_toggle_aria.setIcon(get_icon("power", color="#FF3B30", size=13))
            self.btn_toggle_aria.setProperty("class", "danger-btn")
        else:
            self.status_badge.set_status("OFFLINE // STANDBY", "red")
            self.btn_toggle_aria.setText("ARM ARIA")
            self.btn_toggle_aria.setIcon(get_icon("power", color="#00E575", size=13))
            self.btn_toggle_aria.setProperty("class", "success-btn")

        self.btn_toggle_aria.style().unpolish(self.btn_toggle_aria)
        self.btn_toggle_aria.style().polish(self.btn_toggle_aria)

    _check_daemon_status = _check_aria_status

    def _toggle_aria(self):
        active = self._is_systemd_unit_active()
        cmd = ["systemctl", "--user", "stop" if active else "start", "aria.service"]
        subprocess.run(cmd, capture_output=True)
        QTimer.singleShot(800, self._check_aria_status)

    _toggle_daemon = _toggle_aria

    def _restart_aria(self):
        subprocess.run(["systemctl", "--user", "restart", "aria.service"], capture_output=True)
        QTimer.singleShot(1000, self._check_aria_status)

    _restart_daemon = _restart_aria

    def _summon_hud(self):
        from aria.toggle import toggle
        try:
            toggle()
        except Exception:
            # If ARIA is not running, start it
            self._toggle_aria()
            QTimer.singleShot(1000, toggle)

    def _quick_prompt(self, prompt: str):
        self._summon_hud()

    # ── History & Search ─────────────────────────────────────────────────────
    def _refresh_history(self):
        import sqlite3
        import time
        db_path = config.memory_dir / "memory.db"
        if not db_path.exists():
            return

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, task, summary FROM sessions ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()

        self.table_history.setRowCount(len(rows))
        for i, (ts, task, summary) in enumerate(rows):
            time_str = time.strftime("%b %d, %H:%M", time.localtime(ts)) if ts else "-"
            self.table_history.setItem(i, 0, QTableWidgetItem(time_str))
            self.table_history.setItem(i, 1, QTableWidgetItem(task or "Interactive session"))
            self.table_history.setItem(i, 2, QTableWidgetItem(summary or "In progress / completed"))

    def _filter_history(self, text: str):
        for i in range(self.table_history.rowCount()):
            task_item = self.table_history.item(i, 1)
            summary_item = self.table_history.item(i, 2)
            match = False
            if task_item and text.lower() in task_item.text().lower():
                match = True
            if summary_item and text.lower() in summary_item.text().lower():
                match = True
            self.table_history.setRowHidden(i, not match)

    # ── Dialogs ──────────────────────────────────────────────────────────────
    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()

    def _on_settings_saved(self):
        self.hotkey_pill.setText(f"[ TRIGGER: {config.hotkey.upper()} ]")
        self.info_label.setText(
            f"ENGINE: <b>{config.provider.upper()}</b>  •  "
            f"DISPLAY: <b>{config.display_server.upper()}</b>  •  "
            f"SECURITY: <b>{'PROTECTED' if config.confirm_destructive else 'AUTONOMOUS'}</b>"
        )
        self._check_daemon_status()

    def _open_onboarding(self):
        wizard = OnboardingWizard(self)
        wizard.completed.connect(self._on_settings_saved)
        wizard.exec()
