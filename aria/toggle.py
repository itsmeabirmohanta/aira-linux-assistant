"""
CLI toggle utility to send trigger message to running ARIA service.
Can be mapped in GNOME/KDE/Sway/Hyprland shortcut settings.
"""

import os
import socket
import sys
from pathlib import Path


def toggle():
    sock_path = Path(os.path.expanduser("~/.aria/aria.sock"))
    if not sock_path.exists():
        print("ARIA is not running. Starting ARIA or check systemctl --user status aria.")
        sys.exit(1)

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(str(sock_path))
        client.sendall(b"toggle\n")
        client.close()
    except Exception as e:
        print(f"Error signaling ARIA: {e}")
        sys.exit(1)


if __name__ == "__main__":
    toggle()
