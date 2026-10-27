"""
File system tools for ARIA.
Provides safe, structured file operations:
- read_file
- write_file
- list_directory
- search_files
- delete_file
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from aria.utils.logger import logger


def _resolve_path(path_str: str) -> Path:
    p = Path(os.path.expanduser(path_str))
    if not p.is_absolute():
        p = Path.cwd() / p
    return p.resolve()


def read_file(path: str, max_bytes: int = 100_000) -> Dict[str, Any]:
    """Read contents of a text file up to max_bytes."""
    p = _resolve_path(path)
    if not p.exists():
        return {"error": f"File does not exist: {path}"}
    if not p.is_file():
        return {"error": f"Path is not a regular file: {path}"}

    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        if len(content) > max_bytes:
            truncated = content[:max_bytes]
            return {
                "path": str(p),
                "content": truncated,
                "truncated": True,
                "total_chars": len(content),
            }
        return {"path": str(p), "content": content, "truncated": False}
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}


def write_file(path: str, content: str, mode: str = "w") -> Dict[str, Any]:
    """Write text content to a file (creates parent directories if needed)."""
    p = _resolve_path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        if mode == "a":
            with open(p, "a", encoding="utf-8") as f:
                f.write(content)
        else:
            p.write_text(content, encoding="utf-8")
        return {"success": True, "path": str(p), "bytes_written": len(content.encode("utf-8"))}
    except Exception as e:
        return {"error": f"Failed to write file: {e}"}


def list_directory(path: str = ".", max_items: int = 100) -> Dict[str, Any]:
    """List directory contents with file metadata."""
    p = _resolve_path(path)
    if not p.exists():
        return {"error": f"Directory not found: {path}"}
    if not p.is_dir():
        return {"error": f"Path is not a directory: {path}"}

    items = []
    try:
        for entry in list(p.iterdir())[:max_items]:
            items.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size_bytes": entry.stat().st_size if entry.is_file() else None,
            })
        return {"path": str(p), "items": items, "count": len(items)}
    except Exception as e:
        return {"error": f"Failed to list directory: {e}"}


def search_files(directory: str, pattern: str, max_results: int = 50) -> Dict[str, Any]:
    """Search for files matching a glob pattern."""
    p = _resolve_path(directory)
    if not p.exists() or not p.is_dir():
        return {"error": f"Invalid search directory: {directory}"}

    try:
        matches = [str(match) for match in list(p.glob(pattern))[:max_results]]
        return {"directory": str(p), "pattern": pattern, "matches": matches, "count": len(matches)}
    except Exception as e:
        return {"error": f"Search failed: {e}"}


def delete_file(path: str) -> Dict[str, Any]:
    """Delete a file or empty directory."""
    p = _resolve_path(path)
    if not p.exists():
        return {"error": f"Target not found: {path}"}

    try:
        if p.is_dir():
            p.rmdir()
        else:
            p.unlink()
        return {"success": True, "deleted": str(p)}
    except Exception as e:
        return {"error": f"Failed to delete {path}: {e}"}
