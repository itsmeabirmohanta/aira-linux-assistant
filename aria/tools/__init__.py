"""
Tool registry and definitions for ARIA.
Provides unified tool discovery, schema generation, and dispatch.
"""

from typing import Dict, Any, List
from aria.tools.screen import capture_screen, encode_image_base64
from aria.tools.input_control import input_controller
from aria.tools.filesystem import read_file, write_file, list_directory, search_files, delete_file
from aria.tools.shell import run_shell
from aria.tools.browser import browser_navigate, browser_click, browser_fill, browser_get_text
from aria.tools.voice import voice_recorder

# Set of actions considered destructive that require user confirmation
DESTRUCTIVE_ACTIONS = {
    "delete_file",
    "write_file",
    "run_shell",
    "browser_fill",
}

# Standard OpenAI/Gemini/Claude compatible tool schemas
TOOL_SCHEMAS = [
    {
        "name": "take_screenshot",
        "description": "Capture current screen to inspect windows, errors, or application state.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mouse_click",
        "description": "Click at specific screen coordinates (x, y).",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X coordinate on screen"},
                "y": {"type": "integer", "description": "Y coordinate on screen"},
                "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                "double": {"type": "boolean", "default": False, "description": "Perform double click"},
            },
            "required": ["x", "y"],
        },
    },
    {
        "name": "mouse_move",
        "description": "Move the cursor to target coordinates.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "Target X coordinate"},
                "y": {"type": "integer", "description": "Target Y coordinate"},
            },
            "required": ["x", "y"],
        },
    },
    {
        "name": "type_text",
        "description": "Type text into the currently active or focused input.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to type"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "press_hotkey",
        "description": "Press a key or keyboard shortcut (e.g. ['ctrl', 'c'], ['alt', 'tab'], ['Return']).",
        "parameters": {
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of key names to press together",
                },
            },
            "required": ["keys"],
        },
    },
    {
        "name": "scroll_screen",
        "description": "Scroll mouse wheel up or down.",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["up", "down"], "default": "down"},
                "amount": {"type": "integer", "default": 3, "description": "Number of scroll clicks"},
            },
            "required": ["direction"],
        },
    },
    {
        "name": "run_shell",
        "description": "Execute a bash shell command in the local Linux environment.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Bash command line to run"},
                "cwd": {"type": "string", "default": ".", "description": "Working directory path"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read text content from a file path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write or overwrite content to a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Target file path"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "delete_file",
        "description": "Delete a file or empty directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to delete"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_directory",
        "description": "List files and subdirectories in a directory path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": ".", "description": "Directory path"},
            },
            "required": [],
        },
    },
    {
        "name": "search_files",
        "description": "Search for files by glob pattern.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "default": ".", "description": "Base directory"},
                "pattern": {"type": "string", "description": "Glob pattern (e.g. *.py, **/*.txt)"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "browser_navigate",
        "description": "Open a website in browser.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Web URL to open"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "browser_click",
        "description": "Click an element inside the browser by CSS selector or text.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector or text selector"},
            },
            "required": ["selector"],
        },
    },
    {
        "name": "browser_fill",
        "description": "Fill input in browser by selector.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector"},
                "value": {"type": "string", "description": "Value to input"},
            },
            "required": ["selector", "value"],
        },
    },
    {
        "name": "browser_get_text",
        "description": "Extract text content from the current active browser page.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]
