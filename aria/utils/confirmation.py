"""
Safety and confirmation handling for destructive actions.
"""

from typing import Callable, Dict, Any, Awaitable
from aria.utils.logger import logger
from aria.config import config
from aria.tools import DESTRUCTIVE_ACTIONS


class ConfirmationManager:
    def __init__(self):
        self._prompt_fn: Callable[[str, Dict[str, Any]], Awaitable[bool]] = None

    def register_ui_prompter(self, prompter: Callable[[str, Dict[str, Any]], Awaitable[bool]]):
        """Register async UI confirmation modal/dialog function."""
        self._prompt_fn = prompter

    async def request_confirmation(self, action_name: str, arguments: Dict[str, Any]) -> bool:
        if not config.confirm_destructive:
            return True

        if action_name not in DESTRUCTIVE_ACTIONS:
            return True

        # Special checks for shell commands: only flag potentially destructive commands
        if action_name == "run_shell":
            cmd = arguments.get("command", "").lower()
            safe_read_commands = ("ls", "cat", "echo", "pwd", "which", "grep", "uname", "uptime", "date", "whoami")
            if any(cmd.strip().startswith(sc) for sc in safe_read_commands) and not any(kw in cmd for kw in ("rm", "delete", ">", "sudo")):
                return True

        logger.warning(f"Destructive action intercepted: {action_name} with args {arguments}")
        if self._prompt_fn:
            return await self._prompt_fn(action_name, arguments)

        # Default to safe denial if no prompter registered
        return False


confirmation_manager = ConfirmationManager()
