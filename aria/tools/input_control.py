"""
Input Control Tool for ARIA.
Provides unified mouse, keyboard, and shortcut automation across Wayland and X11:
- Wayland: ydotool + wtype + wl-clipboard
- X11: pyautogui + xdotool
"""

import os
import shutil
import subprocess
import time
from typing import List, Optional, Tuple, Dict, Any
from aria.utils.logger import logger
from aria.config import config


class InputController:
    def __init__(self):
        self.is_wayland = config.display_server == "wayland"
        self.has_ydotool = shutil.which("ydotool") is not None
        self.has_wtype = shutil.which("wtype") is not None
        self._has_pyautogui = False

        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.05
            self._has_pyautogui = True
        except (Exception, SystemExit, BaseException):
            self._has_pyautogui = False

        # Socket check for ydotool
        self._ydotool_socket = os.getenv("YDOTOOL_SOCKET") or f"/run/user/{os.getuid()}/ydotoold.socket"

    def _run_ydotool(self, args: List[str]) -> bool:
        env = os.environ.copy()
        if os.path.exists(self._ydotool_socket):
            env["YDOTOOL_SOCKET"] = self._ydotool_socket
        try:
            res = subprocess.run(["ydotool"] + args, env=env, capture_output=True, timeout=3)
            return res.returncode == 0
        except Exception as e:
            logger.debug(f"ydotool command failed ({args}): {e}")
            return False

    def move_to(self, x: int, y: int) -> bool:
        """Move cursor to absolute coordinates (x, y)."""
        logger.debug(f"Move cursor to ({x}, {y})")
        if self.is_wayland and self.has_ydotool:
            # ydotool mousemove -a x y
            if self._run_ydotool(["mousemove", "-a", str(x), str(y)]):
                return True

        if self._has_pyautogui:
            try:
                import pyautogui
                pyautogui.moveTo(x, y)
                return True
            except Exception as e:
                logger.debug(f"pyautogui moveTo failed: {e}")

        if shutil.which("xdotool"):
            try:
                subprocess.run(["xdotool", "mousemove", str(x), str(y)], timeout=2)
                return True
            except Exception:
                pass
        return False

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left", double: bool = False) -> bool:
        """Click at (x, y) or current location."""
        if x is not None and y is not None:
            self.move_to(x, y)
            time.sleep(0.05)

        btn_map_ydotool = {"left": "0xC0", "right": "0xC1", "middle": "0xC2"}
        btn_code = btn_map_ydotool.get(button.lower(), "0xC0")

        if self.is_wayland and self.has_ydotool:
            clicks = 2 if double else 1
            for _ in range(clicks):
                # click button code
                self._run_ydotool(["click", btn_code])
                if double:
                    time.sleep(0.1)
            return True

        if self._has_pyautogui:
            try:
                import pyautogui
                if double:
                    pyautogui.doubleClick(button=button)
                else:
                    pyautogui.click(button=button)
                return True
            except Exception as e:
                logger.debug(f"pyautogui click failed: {e}")

        if shutil.which("xdotool"):
            btn_num = "1" if button == "left" else "3" if button == "right" else "2"
            cmd = ["xdotool", "click", "--repeat", "2" if double else "1", btn_num]
            try:
                subprocess.run(cmd, timeout=2)
                return True
            except Exception:
                pass

        return False

    def type_text(self, text: str) -> bool:
        """Type arbitrary text into the currently active element."""
        logger.debug(f"Typing text: {text[:30]}...")

        # 1. Try wtype (best for Wayland utf-8 strings)
        if self.is_wayland and self.has_wtype:
            try:
                res = subprocess.run(["wtype", text], capture_output=True, timeout=5)
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        # 2. Try ydotool type
        if self.is_wayland and self.has_ydotool:
            if self._run_ydotool(["type", "--", text]):
                return True

        # 3. Try pyautogui typewrite
        if self._has_pyautogui:
            try:
                import pyautogui
                pyautogui.write(text, interval=0.01)
                return True
            except Exception:
                pass

        # 4. Fallback: copy to clipboard and paste via Ctrl+V
        try:
            if shutil.which("wl-copy"):
                proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                proc.communicate(input=text.encode("utf-8"), timeout=2)
                self.hotkey("ctrl", "v")
                return True
            elif shutil.which("xclip"):
                proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                proc.communicate(input=text.encode("utf-8"), timeout=2)
                self.hotkey("ctrl", "v")
                return True
        except Exception as e:
            logger.debug(f"Clipboard paste fallback failed: {e}")

        return False

    def hotkey(self, *keys: str) -> bool:
        """Press key combination like ('ctrl', 'c'), ('alt', 'tab'), ('Enter',)."""
        logger.debug(f"Sending hotkey: {keys}")
        if self._has_pyautogui:
            try:
                import pyautogui
                pyautogui.hotkey(*[k.lower() for k in keys])
                return True
            except Exception:
                pass

        if self.is_wayland and self.has_wtype:
            try:
                args = ["wtype"]
                for k in keys:
                    args.extend(["-k", k])
                res = subprocess.run(args, capture_output=True, timeout=2)
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        if shutil.which("xdotool"):
            try:
                key_str = "+".join(keys)
                subprocess.run(["xdotool", "key", key_str], timeout=2)
                return True
            except Exception:
                pass

        return False

    def scroll(self, direction: str = "down", amount: int = 3) -> bool:
        """Scroll mouse wheel in given direction ('up' or 'down')."""
        clicks = amount if direction == "up" else -amount
        if self._has_pyautogui:
            try:
                import pyautogui
                pyautogui.scroll(clicks * 100)
                return True
            except Exception:
                pass

        if self.is_wayland and self.has_ydotool:
            # ydotool wheel
            step = str(amount if direction == "up" else -amount)
            return self._run_ydotool(["wheel", "--", step])

        return False

    def set_clipboard(self, text: str) -> bool:
        """Copy text to clipboard."""
        try:
            if shutil.which("wl-copy"):
                proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                proc.communicate(input=text.encode("utf-8"), timeout=2)
                return True
            elif shutil.which("xclip"):
                proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                proc.communicate(input=text.encode("utf-8"), timeout=2)
                return True
        except Exception as e:
            logger.debug(f"set_clipboard failed: {e}")
        return False

    def get_clipboard(self) -> str:
        """Get text from clipboard."""
        try:
            if shutil.which("wl-paste"):
                res = subprocess.run(["wl-paste"], capture_output=True, text=True, timeout=2)
                if res.returncode == 0:
                    return res.stdout
            elif shutil.which("xclip"):
                res = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True, timeout=2)
                if res.returncode == 0:
                    return res.stdout
        except Exception as e:
            logger.debug(f"get_clipboard failed: {e}")
        return ""


input_controller = InputController()
