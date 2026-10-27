"""
Desktop Environment Global Shortcut Registrar for Linux.
Registers global hotkeys natively in GNOME and KDE so that Wayland compositors
intercept the key combination directly, preventing unwanted text entry into active windows.
"""

import shutil
import subprocess
from loguru import logger


def hotkey_to_gnome_binding(hotkey: str) -> str:
    """
    Convert a hotkey string like 'ctrl+space' or 'ctrl+alt+a'
    to GNOME media-keys format e.g. '<Primary>space', '<Primary><Alt>a'.
    """
    parts = [p.strip().lower() for p in hotkey.replace("-", "+").split("+")]
    mods = []
    key = "space"

    for p in parts:
        if p in ("ctrl", "control"):
            mods.append("<Primary>")
        elif p in ("alt", "option"):
            mods.append("<Alt>")
        elif p in ("shift",):
            mods.append("<Shift>")
        elif p in ("super", "win", "meta", "cmd"):
            mods.append("<Super>")
        elif p in ("space", "spacebar"):
            key = "space"
        else:
            key = p

    return "".join(mods) + key


def register_gnome_shortcut(hotkey: str, command: str = "/home/itsmeabirmohanta/.aria/run_gui.sh --toggle") -> bool:
    """
    Register a custom keybinding in GNOME settings daemon.
    Works natively on Ubuntu Wayland without root permissions.
    """
    if not shutil.which("gsettings"):
        return False

    gnome_binding = hotkey_to_gnome_binding(hotkey)
    path = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/aria0/"

    try:
        # 1. Get current custom-keybindings list
        res = subprocess.run(
            ["gsettings", "get", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings"],
            capture_output=True, text=True, timeout=2
        )
        out = res.stdout.strip()
        current_list = []
        if out.startswith("["):
            try:
                import ast
                current_list = ast.literal_eval(out)
            except Exception:
                current_list = []

        if path not in current_list:
            current_list.append(path)
            subprocess.run(
                ["gsettings", "set", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", str(current_list)],
                check=True, timeout=2
            )

        # 2. Set the keybinding properties
        schema = f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{path}"
        subprocess.run(["gsettings", "set", schema, "name", "ARIA Toggle"], check=True, timeout=2)
        subprocess.run(["gsettings", "set", schema, "command", command], check=True, timeout=2)
        subprocess.run(["gsettings", "set", schema, "binding", gnome_binding], check=True, timeout=2)

        logger.success(f"Registered GNOME native shortcut: {hotkey} ({gnome_binding})")
        return True
    except Exception as e:
        logger.warning(f"Could not register GNOME shortcut: {e}")
        return False
