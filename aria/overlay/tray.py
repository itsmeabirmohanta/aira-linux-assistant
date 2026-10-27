"""
System Tray icon and context menu for ARIA — Swiss Modernism 2.0 Edition.
Provides high-precision vector icons, HUD toggle, Control Matrix access,
walkthrough launch, and ARIA state management.
"""

from pathlib import Path
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from aria.utils.logger import logger
from aria.overlay.hud import OverlayHUD
from aria.gui.icons import get_icon, get_pixmap


class SystemTray(QSystemTrayIcon):
    def __init__(self, hud: OverlayHUD, app: QApplication):
        super().__init__()
        self.hud = hud
        self.app = app
        self._dashboard = None
        self.setIcon(self._create_or_load_icon())
        self.setToolTip("ARIA // RESIDENT INTELLIGENCE OS (Ctrl+Space)")

        self._setup_menu()
        self.activated.connect(self._on_tray_activated)

    def _create_or_load_icon(self) -> QIcon:
        icon_path = Path(__file__).resolve().parent.parent.parent / "assets" / "aria_icon.png"
        if icon_path.exists() and icon_path.stat().st_size > 2000:
            return QIcon(str(icon_path))
        # High-resolution vector icon from icon engine
        return get_icon("sparkles", color="#0055FF", size=24)

    def _setup_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #0D0F13;
                color: #E2E6EF;
                border: 1px solid #20242D;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 600;
            }
            QMenu::item {
                padding: 8px 24px 8px 12px;
                border-radius: 3px;
                margin: 2px 0px;
            }
            QMenu::item:selected {
                background-color: #0055FF;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #1F232D;
                margin: 5px 4px;
            }
        """)

        action_toggle = menu.addAction(get_icon("command", color="#0055FF", size=15), "TOGGLE COMMAND HUD  [Ctrl+Space]")
        action_toggle.triggered.connect(self.hud.toggle)

        action_dashboard = menu.addAction(get_icon("screen", color="#CED4E0", size=15), "CONTROL MATRIX DASHBOARD")
        action_dashboard.triggered.connect(self._open_dashboard)

        action_settings = menu.addAction(get_icon("settings", color="#CED4E0", size=15), "CONFIGURATION MATRIX")
        action_settings.triggered.connect(self._open_settings)

        action_walkthrough = menu.addAction(get_icon("compass", color="#CED4E0", size=15), "INTERACTIVE WALKTHROUGH")
        action_walkthrough.triggered.connect(self._open_walkthrough)

        menu.addSeparator()

        action_clear = menu.addAction(get_icon("trash", color="#CED4E0", size=15), "CLEAR HUD TRANSCRIPT")
        action_clear.triggered.connect(self._clear_history)

        action_status = menu.addAction(get_icon("check", color="#00E575", size=15), "STATUS: ONLINE // ARMED")
        action_status.setEnabled(False)

        menu.addSeparator()

        action_quit = menu.addAction(get_icon("power", color="#FF3B30", size=15), "TERMINATE ARIA")
        action_quit.triggered.connect(self.app.quit)

        self.setContextMenu(menu)

    def _open_dashboard(self):
        from aria.gui.dashboard import DashboardWindow
        if self._dashboard is None:
            self._dashboard = DashboardWindow()
        self._dashboard.show()
        self._dashboard.raise_()
        self._dashboard.activateWindow()

    def _open_settings(self):
        from aria.gui.settings_dialog import SettingsDialog
        dialog = SettingsDialog()
        dialog.exec()

    def _open_walkthrough(self):
        from aria.gui.onboarding import OnboardingWizard
        wizard = OnboardingWizard()
        wizard.exec()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.hud.toggle()

    def _clear_history(self):
        self.hud.transcript_view.clear()
        self.hud.transcript_view.setVisible(False)
        self.hud.set_status("[ ● READY ]  HISTORY CLEARED")
