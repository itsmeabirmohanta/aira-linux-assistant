"""
Floating HUD Overlay Window for ARIA.
A Spotlight/Raycast-like glassmorphism interface that appears on hotkey press.
"""

from __future__ import annotations
import asyncio
import os
from typing import Dict, Any, Optional
from pathlib import Path
from aria.utils.logger import logger

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QTextBrowser, QFrame, QDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QKeyEvent, QIcon

from aria.config import config
from aria.agent.core import AgentCore
from aria.agent.memory import Memory
from aria.tools.voice import voice_recorder
from aria.utils.confirmation import confirmation_manager
from aria.gui.icons import get_icon, get_pixmap


class AgentSignalBridge(QObject):
    """Bridge for emitting agent streaming events back to Qt main thread."""
    status_changed = pyqtSignal(str)
    text_chunk = pyqtSignal(str)
    tool_started = pyqtSignal(str, str)
    tool_finished = pyqtSignal(str, str)
    agent_finished = pyqtSignal(str)
    confirmation_requested = pyqtSignal(str, dict, object)  # (action, args, future)
    toggle_requested = pyqtSignal()


class OverlayHUD(QWidget):
    def __init__(self, memory: Memory):
        super().__init__()
        self.memory = memory
        self.agent = AgentCore(memory=memory)
        self.signals = AgentSignalBridge()
        self.is_recording = False
        self._current_task = None

        self._setup_window_properties()
        self._setup_ui()
        self._load_stylesheet()
        self._connect_signals()

        # Register UI confirmation handler
        confirmation_manager.register_ui_prompter(self._prompt_confirmation_async)

    def _setup_window_properties(self):
        self.setObjectName("AriaHUDWindow")
        # Frameless, floating above everything, no taskbar entry
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(config.overlay_width)
        self.setMinimumHeight(140)
        self.setMaximumHeight(520)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(10)

        # Header bar
        header = QFrame()
        header.setObjectName("HeaderBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # Brand glyph + title
        brand_icon = QLabel()
        brand_icon.setFixedSize(20, 20)
        brand_icon.setPixmap(get_pixmap("sparkles", color="#0055FF", size=16))

        logo = QLabel("ARIA // 2.0")
        logo.setObjectName("LogoLabel")

        self.status_label = QLabel("[ ● READY ]  ESC TO DISMISS")
        self.status_label.setObjectName("StatusLabel")

        btn_settings = QPushButton()
        btn_settings.setIcon(get_icon("settings", color="#A0A6B5", size=13))
        btn_settings.setObjectName("IconButton")
        btn_settings.setFixedSize(26, 26)
        btn_settings.setToolTip("Open ARIA Control Center & Settings")
        btn_settings.clicked.connect(self._open_settings)

        btn_close = QPushButton()
        btn_close.setIcon(get_icon("cross", color="#A0A6B5", size=13))
        btn_close.setObjectName("IconButton")
        btn_close.setFixedSize(26, 26)
        btn_close.setToolTip("Close Overlay (Esc)")
        btn_close.clicked.connect(self.hide)

        header_layout.addWidget(brand_icon)
        header_layout.addWidget(logo)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        header_layout.addWidget(btn_settings)
        header_layout.addWidget(btn_close)
        layout.addWidget(header)

        # Input Row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setObjectName("CommandInput")
        self.input_field.setPlaceholderText("ENTER COMMAND, QUERY, OR CODE TASK...")
        self.input_field.returnPressed.connect(self.on_submit)

        self.mic_btn = QPushButton("VOICE")
        self.mic_btn.setIcon(get_icon("mic", color="#FFFFFF", size=14))
        self.mic_btn.setObjectName("MicButton")
        self.mic_btn.setToolTip("Toggle Offline Voice Transcription (faster-whisper)")
        self.mic_btn.clicked.connect(self.toggle_voice_recording)

        self.send_btn = QPushButton("EXEC")
        self.send_btn.setIcon(get_icon("play", color="#090A0D", size=13))
        self.send_btn.setObjectName("IconButton")
        self.send_btn.setFixedHeight(40)
        self.send_btn.clicked.connect(self.on_submit)

        input_row.addWidget(self.input_field)
        input_row.addWidget(self.mic_btn)
        input_row.addWidget(self.send_btn)
        layout.addLayout(input_row)

        # Conversation / Activity view
        self.transcript_view = QTextBrowser()
        self.transcript_view.setObjectName("TranscriptView")
        self.transcript_view.setOpenExternalLinks(True)
        self.transcript_view.setVisible(False)  # expand when there's content
        layout.addWidget(self.transcript_view)

    def _load_stylesheet(self):
        qss_path = Path(__file__).parent / "styles.qss"
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text())

    def _center_on_screen(self):
        screen = self.screen() or self.window().screen()
        if screen:
            screen_geo = screen.geometry()
            x = screen_geo.x() + (screen_geo.width() - self.width()) // 2
            y = screen_geo.y() + 80  # 80px from top of screen
            self.move(x, y)

    def _connect_signals(self):
        self.signals.status_changed.connect(self.set_status)
        self.signals.text_chunk.connect(self.append_text)
        self.signals.tool_started.connect(self.on_tool_started)
        self.signals.tool_finished.connect(self.on_tool_finished)
        self.signals.agent_finished.connect(self.on_agent_finished)
        self.signals.confirmation_requested.connect(self._show_confirmation_dialog)
        self.signals.toggle_requested.connect(self._do_toggle)

    def toggle(self):
        """Thread-safe toggle callable from any thread (pynput, socket, etc)."""
        self.signals.toggle_requested.emit()

    def _do_toggle(self):
        """Actual UI visibility toggle executed strictly on Qt main thread."""
        if self.isVisible():
            self.hide()
        else:
            self._center_on_screen()
            self.show()
            self.raise_()
            self.activateWindow()
            self.input_field.setFocus()

    def _open_settings(self):
        from aria.gui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def set_status(self, text: str):
        self.status_label.setText(text)

    def append_text(self, text: str):
        self.transcript_view.setVisible(True)
        self.transcript_view.append(text)
        # Scroll to bottom
        cursor = self.transcript_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.transcript_view.setTextCursor(cursor)

    def on_tool_started(self, tool_name: str, args_str: str):
        self.set_status(f"[ ⚡ EXEC: {tool_name.upper()} ]")
        self.append_text(f"<div style='margin-top: 4px; font-family: monospace; color: #3B82F6;'>▶ <b>EXEC // {tool_name.upper()}</b> <span style='color: #6C7383;'>{args_str}</span></div>")

    def on_tool_finished(self, tool_name: str, result_summary: str):
        self.append_text(f"<div style='font-family: monospace; color: #00E575;'>✓ <b>DONE // {tool_name.upper()}</b></div>")

    def on_agent_finished(self, final_text: str):
        self.set_status("[ ● READY ]")
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()

    def on_submit(self):
        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.transcript_view.setVisible(True)

        self.append_text(f"<div style='margin-top: 10px; font-family: monospace; color: #FFFFFF;'><b>USER //</b> {text}</div>")
        self.set_status("[ ⏳ PROCESSING ]")

        # Run async agent in background thread loop
        asyncio.create_task(self._run_agent_task(text))

    async def _run_agent_task(self, prompt: str):
        try:
            async for event in self.agent.run(prompt):
                etype = event.get("type")
                if etype == "status":
                    self.signals.status_changed.emit(f"[ ⚙️ {event.get('message', '').upper()} ]")
                elif etype == "text":
                    self.signals.text_chunk.emit(
                        f"<div style='margin-top: 6px; font-family: monospace; color: #D1D5DB;'><b style='color: #0055FF;'>ARIA //</b> {event.get('content')}</div>"
                    )
                elif etype == "tool_start":
                    self.signals.tool_started.emit(event.get("tool", ""), str(event.get("args", {})))
                elif etype == "tool_end":
                    self.signals.tool_finished.emit(event.get("tool", ""), str(event.get("result", {}))[:80])
                elif etype == "done":
                    self.signals.agent_finished.emit(event.get("content", ""))
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            self.signals.text_chunk.emit(f"<div style='color: #FF3B30; font-family: monospace;'>ERR // {e}</div>")
            self.signals.agent_finished.emit("")

    def toggle_voice_recording(self):
        if not self.is_recording:
            # Start recording
            success = voice_recorder.start()
            if success:
                self.is_recording = True
                self.mic_btn.setProperty("recording", "true")
                self.mic_btn.setStyleSheet("background-color: #DC2626; color: white;")
                self.set_status("🔴 Listening... Click mic again to finish")
        else:
            # Stop and transcribe
            self.is_recording = False
            self.mic_btn.setProperty("recording", "false")
            self.mic_btn.setStyleSheet("")
            self.set_status("Transcribing voice input...")

            def _transcribe():
                text = voice_recorder.stop_and_transcribe()
                if text:
                    self.input_field.setText(text)
                    self.on_submit()
                else:
                    self.set_status("No speech recognized. Ready.")

            QTimer.singleShot(100, _transcribe)

    async def _prompt_confirmation_async(self, action_name: str, arguments: Dict[str, Any]) -> bool:
        """Handle destructive action prompt by creating a future resolved on Qt thread."""
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.signals.confirmation_requested.emit(action_name, arguments, future)
        return await future

    def _show_confirmation_dialog(self, action_name: str, arguments: dict, future):
        """Qt modal confirmation dialog for safety approval."""
        dialog = QDialog(self)
        dialog.setObjectName("ConfirmationDialog")
        dialog.setWindowTitle("SAFETY PROTOCOL // CONFIRMATION REQUIRED")
        dialog.setFixedWidth(480)

        vbox = QVBoxLayout(dialog)
        vbox.setContentsMargins(20, 20, 20, 20)
        vbox.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        alert_icon = QLabel()
        alert_icon.setFixedSize(20, 20)
        alert_icon.setPixmap(get_pixmap("alert", color="#FF3B30", size=18))
        title = QLabel(f"SAFETY PROTOCOL // INTERCEPT: {action_name.upper()}")
        title.setStyleSheet("color: #FF3B30; font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 800; letter-spacing: 0.5px;")
        header_row.addWidget(alert_icon)
        header_row.addWidget(title)
        header_row.addStretch()
        vbox.addLayout(header_row)

        desc = QLabel("An autonomous action classified as potentially destructive has been intercepted. Verify arguments before authorization:")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8D93A0; font-size: 12px; line-height: 1.4;")
        vbox.addWidget(desc)

        args_box = QTextBrowser()
        args_box.setFixedHeight(90)
        args_box.setStyleSheet("background-color: #07080A; border: 1px solid #1F232D; border-radius: 4px; color: #E2E6EF; font-family: 'JetBrains Mono', monospace; font-size: 11px; padding: 8px;")
        args_box.setPlainText(str(arguments))
        vbox.addWidget(args_box)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        btn_deny = QPushButton("DENY / ABORT")
        btn_deny.setIcon(get_icon("cross", color="#CED4E0", size=13))
        btn_deny.setObjectName("CancelButton")
        btn_allow = QPushButton("AUTHORIZE EXECUTION ➔")
        btn_allow.setIcon(get_icon("shield_check", color="#FFFFFF", size=13))
        btn_allow.setObjectName("DangerButton")

        btn_box.addStretch()
        btn_box.addWidget(btn_deny)
        btn_box.addWidget(btn_allow)
        vbox.addLayout(btn_box)

        def on_allow():
            future.set_result(True)
            dialog.accept()

        def on_deny():
            future.set_result(False)
            dialog.reject()

        btn_allow.clicked.connect(on_allow)
        btn_deny.clicked.connect(on_deny)
        dialog.exec()
