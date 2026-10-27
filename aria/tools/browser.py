"""
Browser automation tool for ARIA using Playwright.
Allows the agent to navigate, click, fill forms, extract text, and capture web pages.
"""

import asyncio
import shutil
import subprocess
from typing import Dict, Any, Optional
from aria.utils.logger import logger

_playwright_instance = None
_browser_instance = None
_page_instance = None


async def get_browser_page():
    """Lazily initialize and return persistent Playwright page."""
    global _playwright_instance, _browser_instance, _page_instance
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None

    if _page_instance is not None and not _page_instance.is_closed():
        return _page_instance

    try:
        _playwright_instance = await async_playwright().start()
        _browser_instance = await _playwright_instance.chromium.launch(
            headless=False,  # Visible so the user can watch the agent work!
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        _page_instance = await _browser_instance.new_page()
        await _page_instance.set_viewport_size({"width": 1280, "height": 800})
        return _page_instance
    except Exception as e:
        logger.warning(f"Could not initialize Playwright: {e}")
        return None


async def browser_navigate(url: str) -> Dict[str, Any]:
    """Navigate to a URL in browser."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    page = await get_browser_page()
    if page:
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            title = await page.title()
            return {"success": True, "url": page.url, "title": title, "status": response.status if response else 200}
        except Exception as e:
            return {"error": f"Failed to navigate: {e}"}

    # Fallback to system default browser via xdg-open
    if shutil.which("xdg-open"):
        subprocess.Popen(["xdg-open", url])
        return {"success": True, "opened_with": "xdg-open", "url": url}

    return {"error": "Neither Playwright nor xdg-open is available."}


async def browser_click(selector: str) -> Dict[str, Any]:
    """Click an element on the active browser page."""
    page = await get_browser_page()
    if not page:
        return {"error": "Browser is not active."}
    try:
        await page.click(selector, timeout=5000)
        return {"success": True, "clicked": selector}
    except Exception as e:
        return {"error": f"Failed to click '{selector}': {e}"}


async def browser_fill(selector: str, value: str) -> Dict[str, Any]:
    """Fill text into an input field on the page."""
    page = await get_browser_page()
    if not page:
        return {"error": "Browser is not active."}
    try:
        await page.fill(selector, value, timeout=5000)
        return {"success": True, "filled": selector, "value": value}
    except Exception as e:
        return {"error": f"Failed to fill '{selector}': {e}"}


async def browser_get_text(max_chars: int = 5000) -> Dict[str, Any]:
    """Extract visible text content from the current web page."""
    page = await get_browser_page()
    if not page:
        return {"error": "Browser is not active."}
    try:
        text = await page.inner_text("body")
        return {"success": True, "url": page.url, "text": text[:max_chars]}
    except Exception as e:
        return {"error": f"Failed to extract text: {e}"}


async def close_browser():
    """Cleanly close browser session."""
    global _playwright_instance, _browser_instance, _page_instance
    try:
        if _page_instance:
            await _page_instance.close()
        if _browser_instance:
            await _browser_instance.close()
        if _playwright_instance:
            await _playwright_instance.stop()
    except Exception:
        pass
    _page_instance = None
    _browser_instance = None
    _playwright_instance = None
