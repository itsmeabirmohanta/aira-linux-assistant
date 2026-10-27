"""
ARIA — Autonomous Resident Intelligence Agent
Main entry point: starts the ARIA background service, system tray,
registers the global hotkey listener, and integrates the Qt/asyncio event loop.
"""

import sys
import os
import signal
import asyncio
from aria.utils.logger import logger, setup_logger

# Wayland display environment configuration
os.environ.setdefault("QT_QPA_PLATFORM", "wayland;xcb")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from aria.config import config
from aria.hotkey import HotkeyManager
from aria.overlay.hud import OverlayHUD
from aria.overlay.tray import SystemTray
from aria.agent.memory import Memory
from aria.utils.logger import setup_logger


def main():
    if "--gui" in sys.argv or "--dashboard" in sys.argv:
        from aria.gui.app import run_app
        run_app()
        return
    elif "--settings" in sys.argv or "-s" in sys.argv:
        from aria.gui.app import run_app
        run_app()
        return
    elif "--onboarding" in sys.argv or "-w" in sys.argv:
        from aria.gui.app import run_app
        run_app()
        return

    setup_logger()
    logger.info("Starting ARIA — Autonomous Resident Intelligence Agent")
    logger.info(f"AI Provider: {config.provider}")
    logger.info(f"Hotkey: {config.hotkey}")
    logger.info(f"Display server: {config.display_server}")

    # Warn about unconfigured keys
    warnings = config.validate()
    for w in warnings:
        logger.warning(w)

    # Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("ARIA")
    app.setApplicationDisplayName("ARIA Agent")
    app.setQuitOnLastWindowClosed(False)  # Keep running in background when HUD is hidden

    # Initialise memory
    memory = Memory()

    # Create overlay HUD (hidden initially)
    hud = OverlayHUD(memory=memory)

    # System tray icon
    tray = SystemTray(hud=hud, app=app)
    tray.show()

    # Global hotkey & IPC trigger
    hotkey_mgr = HotkeyManager(
        hotkey=config.hotkey,
        on_activate=hud.toggle,
    )
    hotkey_mgr.start()

    loop = None

    # Graceful shutdown handler
    def shutdown(*_):
        logger.info("Shutting down ARIA...")
        try:
            hotkey_mgr.stop()
        except Exception:
            pass
        try:
            tray.hide()
        except Exception:
            pass
        try:
            if loop and loop.is_running():
                loop.stop()
        except Exception:
            pass
        app.quit()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logger.success("ARIA is ready! Press Ctrl+Space to toggle the assistant overlay.")

    # Run with qasync if available, or standard Qt event loop
    try:
        import qasync
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        with loop:
            loop.run_forever()
    except ImportError:
        logger.debug("qasync not detected, starting standard Qt loop.")
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
