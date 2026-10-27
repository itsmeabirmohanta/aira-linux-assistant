"""
ARIA Desktop Application Entry Point — Swiss Modernism 2.0 Edition.
Automatically launches the Interactive Walkthrough on first launch / post-install,
or opens the Dashboard / Settings directly.
"""

import sys
import os
import argparse
from pathlib import Path

# Wayland display environment configuration
os.environ.setdefault("QT_QPA_PLATFORM", "wayland;xcb")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from aria.config import config
from aria.gui.dashboard import DashboardWindow
from aria.gui.onboarding import OnboardingWizard
from aria.gui.settings_dialog import SettingsDialog
from aria.gui.icons import get_icon
from aria.utils.logger import setup_logger, logger


def run_app():
    if "--toggle" in sys.argv or "-t" in sys.argv:
        from aria.toggle import toggle
        toggle()
        return

    setup_logger()
    parser = argparse.ArgumentParser(description="ARIA Desktop GUI")
    parser.add_argument("--settings", "-s", action="store_true", help="Open Settings dialog directly")
    parser.add_argument("--onboarding", "-w", action="store_true", help="Force run the onboarding setup wizard")
    parser.add_argument("--walkthrough", action="store_true", help="Force run the interactive walkthrough tour")
    parser.add_argument("--toggle", "-t", action="store_true", help="Toggle floating HUD overlay")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("ARIA")
    app.setApplicationDisplayName("ARIA Control Center")

    # Set Application Icon
    icon_path = Path(__file__).resolve().parent.parent.parent / "assets" / "aria_icon.png"
    if icon_path.exists() and icon_path.stat().st_size > 2000:
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        app.setWindowIcon(get_icon("sparkles", color="#0055FF", size=32))

    # Check if first run / walkthrough needed
    walkthrough_flag = config.memory_dir / ".walkthrough_done"
    needs_walkthrough = (
        args.walkthrough or
        args.onboarding or
        not walkthrough_flag.exists()
    )

    dashboard = DashboardWindow()

    if args.settings:
        dialog = SettingsDialog()
        dialog.exec()
        sys.exit(0)

    if needs_walkthrough:
        wizard = OnboardingWizard()
        wizard.completed.connect(dashboard.show)
        wizard.exec()
        if not wizard.result():
            # If user dismissed wizard without completing, still open dashboard
            dashboard.show()
    else:
        dashboard.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
