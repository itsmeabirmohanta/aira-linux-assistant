"""
Shell execution tool for ARIA.
Executes bash commands with timeout, working directory, and stdout/stderr capture.
"""

import subprocess
import os
from typing import Dict, Any
from aria.utils.logger import logger


def run_shell(command: str, cwd: str = ".", timeout_seconds: int = 30) -> Dict[str, Any]:
    """
    Execute a shell command via bash.
    Returns returncode, stdout, and stderr.
    """
    logger.info(f"Executing shell command: {command}")
    expanded_cwd = os.path.expanduser(cwd)
    if not os.path.exists(expanded_cwd):
        expanded_cwd = os.getcwd()

    try:
        proc = subprocess.run(
            ["bash", "-c", command],
            cwd=expanded_cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return {
            "command": command,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-10000:],  # limit output size to avoid blowing LLM context
            "stderr": proc.stderr[-5000:],
            "success": proc.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "returncode": -1,
            "error": f"Command timed out after {timeout_seconds} seconds.",
            "success": False,
        }
    except Exception as e:
        return {
            "command": command,
            "returncode": -1,
            "error": str(e),
            "success": False,
        }
