"""
Global Hotkey Manager for ARIA.
Supports:
1. pynput global key listener for direct background capture
2. Unix domain socket listener (~/.aria/aria.sock) so desktop environment native
   shortcuts (e.g. GNOME Settings -> Custom Shortcut -> python -m aria.toggle)
   can reliably toggle ARIA instantly even under strict Wayland compositors!
"""

from __future__ import annotations
import os
import socket
import threading
from typing import Callable, Optional
from pathlib import Path
from aria.utils.logger import logger

try:
    from pynput import keyboard
except ImportError:
    keyboard = None


class HotkeyManager:
    def __init__(self, hotkey: str, on_activate: Callable[[], None]):
        self.hotkey_str = hotkey.strip()
        self.on_activate = on_activate
        self.listener: Optional[keyboard.GlobalHotKeys] = None
        self._running = False
        self._socket_thread: Optional[threading.Thread] = None
        self._socket_path = Path(os.path.expanduser("~/.aria/aria.sock"))

    def _normalize_hotkey(self, key_str: str) -> str:
        """
        Convert user friendly strings like 'ctrl+space' into pynput format '<ctrl>+<space>'
        """
        parts = [p.strip().lower() for p in key_str.replace("-", "+").split("+")]
        norm_parts = []
        for p in parts:
            if p in ("ctrl", "control"):
                norm_parts.append("<ctrl>")
            elif p in ("alt", "option"):
                norm_parts.append("<alt>")
            elif p in ("shift",):
                norm_parts.append("<shift>")
            elif p in ("super", "win", "cmd", "meta"):
                norm_parts.append("<cmd>")
            elif p in ("space", "spacebar"):
                norm_parts.append("<space>")
            else:
                norm_parts.append(p)
        return "+".join(norm_parts)

    def _start_socket_listener(self):
        """IPC socket listener for instant triggers from CLI or desktop shortcuts."""
        self._socket_path.parent.mkdir(parents=True, exist_ok=True)
        if self._socket_path.exists():
            try:
                self._socket_path.unlink()
            except OSError:
                pass

        def socket_worker():
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                server.bind(str(self._socket_path))
                server.listen(5)
                server.settimeout(1.0)
                while self._running:
                    try:
                        conn, _ = server.accept()
                        with conn:
                            msg = conn.recv(1024).decode().strip()
                            if msg in ("toggle", "show", "activate"):
                                logger.info(f"Received IPC trigger '{msg}' -> activating overlay HUD")
                                self.on_activate()
                    except socket.timeout:
                        continue
                    except Exception as e:
                        if self._running:
                            logger.debug(f"IPC socket accept error: {e}")
            finally:
                try:
                    server.close()
                    if self._socket_path.exists():
                        self._socket_path.unlink()
                except Exception:
                    pass

        self._socket_thread = threading.Thread(target=socket_worker, daemon=True)
        self._socket_thread.start()
        logger.info(f"IPC trigger socket listening on {self._socket_path}")

    def start(self):
        self._running = True
        self._start_socket_listener()

        if keyboard is None:
            logger.warning("pynput is not installed; global keyboard hook disabled. IPC socket available.")
            return

        norm_key = self._normalize_hotkey(self.hotkey_str)
        logger.info(f"Registering global hotkey: '{self.hotkey_str}' -> '{norm_key}'")

        try:
            hotkey_map = {norm_key: self._on_triggered}
            self.listener = keyboard.GlobalHotKeys(hotkey_map)
            self.listener.start()
            logger.success(f"Global hotkey {self.hotkey_str} registered successfully.")
        except Exception as e:
            logger.warning(
                f"Could not bind direct pynput hotkey ({e}). "
                "Under Wayland, you can bind a GNOME/KDE shortcut to run 'python3 -m aria.toggle'."
            )

    def _on_triggered(self):
        logger.info(f"Hotkey '{self.hotkey_str}' triggered -> activating overlay HUD")
        self.on_activate()

    def stop(self):
        self._running = False
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None
        if self._socket_path.exists():
            try:
                self._socket_path.unlink()
            except Exception:
                pass
        logger.info("Hotkey manager stopped.")
