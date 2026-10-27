"""
GUI Instantiation & Functional Test Suite.
Verifies offscreen creation and logic for:
1. DashboardWindow
2. SettingsDialog & HotkeyPicker
3. OnboardingWizard
"""

import os
import sys
from pathlib import Path

# Ensure offscreen Qt platform for testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtWidgets import QApplication
from aria.gui.dashboard import DashboardWindow
from aria.gui.settings_dialog import SettingsDialog
from aria.gui.onboarding import OnboardingWizard
from aria.gui.widgets import HotkeyPicker, ActionCard, StatusBadge, ToggleSwitch, SettingRow


def test_gui_components():
    app = QApplication.instance() or QApplication(sys.argv)

    print("🖼️  [1/4] Testing GUI Custom Widgets...")
    badge = StatusBadge(text="Active", status="green")
    assert "ACTIVE" in badge.text()

    switch = ToggleSwitch(checked=True)
    assert switch.isChecked() is True

    card = ActionCard(icon="⚡", title="Test Action", subtitle="Test Subtitle")
    assert card is not None

    picker = HotkeyPicker(initial_hotkey="ctrl+space")
    assert picker.value() == "ctrl+space"
    picker.setValue("Ctrl+Alt+T")
    assert "ctrl+alt+t" in picker.value()
    print("   ✅ Custom widgets created successfully.")

    print("⚙️  [2/4] Testing SettingsDialog & HotkeyPicker...")
    settings = SettingsDialog()
    assert settings.provider_select.count() >= 4
    # Test setting values
    settings.picker_hotkey.setValue("ctrl+alt+a")
    assert settings.picker_hotkey.value() == "ctrl+alt+a"
    print("   ✅ SettingsDialog loaded with providers and hotkey picker.")

    print("🚀 [3/4] Testing OnboardingWizard...")
    wizard = OnboardingWizard()
    assert wizard.stack.count() == 5  # 5 steps
    print(f"   Wizard loaded {wizard.stack.count()} onboarding steps.")
    # Navigate to step 2
    wizard._go_next()
    assert wizard.stack.currentIndex() == 1
    # Navigate back
    wizard._go_back()
    assert wizard.stack.currentIndex() == 0
    print("   ✅ OnboardingWizard 5-step navigation verified.")

    print("📊 [4/4] Testing DashboardWindow...")
    dashboard = DashboardWindow()
    assert dashboard.table_history is not None
    assert dashboard.status_badge is not None
    assert dashboard.info_label is not None
    dashboard._check_daemon_status()
    dashboard._refresh_history()
    print("   ✅ DashboardWindow instantiated and populated.")

    print("🎨 [5/5] Testing Professional Vector Icon Engine & Tray...")
    from aria.gui.icons import SVG_PATHS, get_icon, get_pixmap
    for name in SVG_PATHS:
        pix = get_pixmap(name, color="#0055FF", size=24)
        assert not pix.isNull(), f"Failed rendering icon {name}"
        icon = get_icon(name)
        assert not icon.isNull(), f"Failed creating QIcon {name}"
    print(f"   ✅ All {len(SVG_PATHS)} vector SVG icons verified at native DPI.")

    from aria.overlay.hud import OverlayHUD
    from aria.agent.memory import Memory
    from aria.overlay.tray import SystemTray
    mem = Memory()
    hud = OverlayHUD(memory=mem)
    tray = SystemTray(hud=hud, app=app)
    assert tray.contextMenu() is not None
    assert len(tray.contextMenu().actions()) >= 6
    print("   ✅ SystemTray with vector action icons verified.")

    print("\n🎉 ALL GUI COMPONENTS, ICONS & WALKTHROUGH TESTS PASSED!")


if __name__ == "__main__":
    test_gui_components()
