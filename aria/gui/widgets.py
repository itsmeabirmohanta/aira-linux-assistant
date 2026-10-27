"""
Reusable Swiss Modernism 2.0 UI components for the ARIA Desktop GUI.
Includes architectural cards, geometric toggle switches, technical status badges, and setting rows.
Integrated with high-precision vector SVG icons and mathematical padding layouts.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QKeySequenceEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QFont, QPaintEvent, QKeySequence

from aria.gui.icons import get_pixmap, get_icon, SVG_PATHS


class ToggleSwitch(QWidget):
    """Swiss Modernism 2.0 precision mechanical sliding toggle switch."""
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedSize(48, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = checked
        self._thumb_position = 25.0 if checked else 3.0

        self._anim = QPropertyAnimation(self, b"thumb_position", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def get_thumb_position(self) -> float:
        return self._thumb_position

    def set_thumb_position(self, pos: float):
        self._thumb_position = pos
        self.update()

    thumb_position = pyqtProperty(float, get_thumb_position, set_thumb_position)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self._anim.stop()
            self._anim.setStartValue(self._thumb_position)
            self._anim.setEndValue(25.0 if checked else 3.0)
            self._anim.start()
            self.toggled.emit(checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track background (Swiss Cobalt when active, deep carbon when inactive)
        track_color = QColor(0, 85, 255) if self._checked else QColor(20, 23, 30)
        border_color = QColor(0, 85, 255) if self._checked else QColor(42, 46, 58)

        painter.setBrush(track_color)
        painter.setPen(border_color)
        painter.drawRoundedRect(0, 0, self.width() - 1, self.height() - 1, 4, 4)

        # Thumb (crisp white geometric slider)
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(int(self._thumb_position), 3, 20, 18, 3, 3)
        painter.end()


class StatusBadge(QLabel):
    """Swiss technical status badge with signal pip."""
    def __init__(self, text: str = "Active", status: str = "green", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status(text, status)

    def set_status(self, text: str, status: str = "green"):
        pip = "●"
        if status == "green":
            self.setText(f"{pip}  {text.upper()}")
            self.setProperty("class", "badge-green")
        elif status == "purple":
            self.setText(f"■  {text.upper()}")
            self.setProperty("class", "badge-purple")
        else:
            self.setText(f"▲  {text.upper()}")
            self.setProperty("class", "badge-red")
        self.style().unpolish(self)
        self.style().polish(self)


class SettingRow(QFrame):
    """Swiss architectural setting row with Title, Description, and Widget."""
    def __init__(self, title: str, description: str, widget: QWidget, icon_name: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(18)

        if icon_name and icon_name in SVG_PATHS:
            icon_box = QLabel()
            icon_box.setFixedSize(32, 32)
            icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_box.setStyleSheet(
                "background-color: #141720; border: 1px solid #242936; border-radius: 4px;"
            )
            icon_box.setPixmap(get_pixmap(icon_name, color="#CED4E0", size=16))
            layout.addWidget(icon_box)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_lbl = QLabel(title.upper())
        title_lbl.setProperty("class", "heading-3")

        desc_lbl = QLabel(description)
        desc_lbl.setProperty("class", "subtitle")
        desc_lbl.setWordWrap(True)

        text_layout.addWidget(title_lbl)
        text_layout.addWidget(desc_lbl)

        layout.addLayout(text_layout, stretch=1)
        layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


class ActionCard(QFrame):
    """
    Swiss modular action card with numbered index, architectural icon container,
    and responsive hover states.
    """
    clicked = pyqtSignal()

    def __init__(self, icon: str, title: str, subtitle: str, index: str = "01", parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # Header with index number and professional vector icon box
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        idx_lbl = QLabel(f"// {index}")
        idx_lbl.setProperty("class", "tech-label")
        top_row.addWidget(idx_lbl)
        top_row.addStretch()

        # Architectural icon box (34x34px)
        icon_box = QLabel()
        icon_box.setFixedSize(34, 34)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if icon in SVG_PATHS:
            icon_box.setStyleSheet(
                "background-color: #141720; border: 1px solid #232734; border-radius: 4px;"
            )
            icon_box.setPixmap(get_pixmap(icon, color="#0055FF", size=18))
        else:
            icon_box.setText(icon)
            icon_box.setFont(QFont("Inter", 13))
            icon_box.setStyleSheet(
                "background-color: #141720; border: 1px solid #232734; border-radius: 4px; color: #FFFFFF;"
            )

        top_row.addWidget(icon_box)
        layout.addLayout(top_row)

        title_lbl = QLabel(title.upper())
        title_lbl.setProperty("class", "heading-3")

        sub_lbl = QLabel(subtitle)
        sub_lbl.setProperty("class", "subtitle")
        sub_lbl.setWordWrap(True)

        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class HotkeyPicker(QWidget):
    """
    Swiss precision shortcut recorder widget using QKeySequenceEdit.
    Captures any key combination with monospace styling, keyboard icon, and 1-click Swiss pills.
    """
    hotkeyChanged = pyqtSignal(str)

    def __init__(self, initial_hotkey: str = "ctrl+space", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Keyboard vector icon
        kb_icon = QLabel()
        kb_icon.setFixedSize(28, 28)
        kb_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        kb_icon.setStyleSheet("background-color: #141720; border: 1px solid #232734; border-radius: 4px;")
        kb_icon.setPixmap(get_pixmap("keyboard", color="#CED4E0", size=15))
        layout.addWidget(kb_icon)

        # Native Qt KeySequenceEdit with monospace font
        self.kse = QKeySequenceEdit(QKeySequence(initial_hotkey))
        self.kse.setFixedWidth(160)
        self.kse.setFont(QFont("JetBrains Mono", 11, QFont.Weight.Bold))
        self.kse.setToolTip("Click to record shortcut key sequence")
        self.kse.keySequenceChanged.connect(self._on_seq_changed)
        layout.addWidget(self.kse)

        # Quick 1-click preset pills
        presets = ["Ctrl+Space", "Alt+Space", "Super+Space", "Ctrl+Alt+A"]
        for p in presets:
            btn = QPushButton(f"[{p}]")
            btn.setProperty("class", "ghost-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("JetBrains Mono", 10, QFont.Weight.Bold))
            btn.setToolTip(f"Set shortcut to {p}")
            btn.setStyleSheet(
                "padding: 5px 8px; font-size: 11px; font-weight: 700; "
                "border-radius: 3px; background-color: #141720; color: #CED4E0; "
                "border: 1px solid #282D3A;"
            )
            btn.clicked.connect(lambda _, preset=p: self.setValue(preset))
            layout.addWidget(btn)

    def _on_seq_changed(self, seq: QKeySequence):
        str_val = seq.toString().lower().replace(" ", "")
        if str_val:
            self.hotkeyChanged.emit(str_val)

    def value(self) -> str:
        s = self.kse.keySequence().toString().lower().replace(" ", "")
        return s or "ctrl+space"

    def setValue(self, hotkey: str):
        self.kse.setKeySequence(QKeySequence(hotkey))
        self.hotkeyChanged.emit(hotkey.lower().replace(" ", ""))
