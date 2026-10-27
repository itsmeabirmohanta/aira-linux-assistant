"""
Tool execution dispatcher for ARIA.
Dispatches tool calls to actual functions, checks safety, and formats results.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from aria.utils.logger import logger
from aria.providers.base import ToolCall
from aria.utils.confirmation import confirmation_manager
from aria.tools.screen import capture_screen
from aria.tools.input_control import input_controller
from aria.tools.filesystem import read_file, write_file, list_directory, search_files, delete_file
from aria.tools.shell import run_shell
from aria.tools.browser import browser_navigate, browser_click, browser_fill, browser_get_text


class ToolExecutor:
    async def execute(self, tool_call: ToolCall) -> Dict[str, Any]:
        name = tool_call.name
        args = tool_call.arguments
        logger.info(f"Executing tool '{name}' with args {args}")

        # Check safety confirmation
        allowed = await confirmation_manager.request_confirmation(name, args)
        if not allowed:
            return {
                "success": False,
                "error": f"Action '{name}' was rejected by the user for safety reasons.",
            }

        try:
            if name == "take_screenshot":
                img = capture_screen()
                return {"success": True, "message": f"Captured screenshot ({img.width}x{img.height})", "_image": img}

            elif name == "mouse_click":
                x = int(args.get("x", 0))
                y = int(args.get("y", 0))
                btn = args.get("button", "left")
                double = bool(args.get("double", False))
                success = input_controller.click(x=x, y=y, button=btn, double=double)
                return {"success": success, "clicked_at": (x, y)}

            elif name == "mouse_move":
                x = int(args.get("x", 0))
                y = int(args.get("y", 0))
                success = input_controller.move_to(x, y)
                return {"success": success, "moved_to": (x, y)}

            elif name == "type_text":
                text = str(args.get("text", ""))
                success = input_controller.type_text(text)
                return {"success": success, "typed_length": len(text)}

            elif name == "press_hotkey":
                keys = args.get("keys", [])
                success = input_controller.hotkey(*keys)
                return {"success": success, "keys_pressed": keys}

            elif name == "scroll_screen":
                direction = args.get("direction", "down")
                amount = int(args.get("amount", 3))
                success = input_controller.scroll(direction=direction, amount=amount)
                return {"success": success, "scrolled": direction}

            elif name == "run_shell":
                cmd = str(args.get("command", ""))
                cwd = str(args.get("cwd", "."))
                return run_shell(command=cmd, cwd=cwd)

            elif name == "read_file":
                path = str(args.get("path", ""))
                return read_file(path)

            elif name == "write_file":
                path = str(args.get("path", ""))
                content = str(args.get("content", ""))
                return write_file(path, content)

            elif name == "delete_file":
                path = str(args.get("path", ""))
                return delete_file(path)

            elif name == "list_directory":
                path = str(args.get("path", "."))
                return list_directory(path)

            elif name == "search_files":
                directory = str(args.get("directory", "."))
                pattern = str(args.get("pattern", "*"))
                return search_files(directory, pattern)

            elif name == "browser_navigate":
                url = str(args.get("url", ""))
                return await browser_navigate(url)

            elif name == "browser_click":
                selector = str(args.get("selector", ""))
                return await browser_click(selector)

            elif name == "browser_fill":
                selector = str(args.get("selector", ""))
                val = str(args.get("value", ""))
                return await browser_fill(selector, val)

            elif name == "browser_get_text":
                return await browser_get_text()

            else:
                return {"error": f"Unknown tool: '{name}'"}

        except Exception as e:
            logger.error(f"Error during tool '{name}' execution: {e}")
            return {"error": str(e), "success": False}


tool_executor = ToolExecutor()
