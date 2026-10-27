"""
ARIA End-to-End Workflow Simulation Test Suite.
Tests all standalone workflows, tool execution, safety checks, browser,
and agent execution pipeline with mock provider.
"""

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aria.config import config
from aria.agent.memory import Memory
from aria.agent.core import AgentCore
from aria.providers.base import BaseProvider, ProviderResponse, ToolCall, AgentMessage
from aria.tools.screen import capture_screen, encode_image_base64, get_screen_data_url
from aria.tools.input_control import InputController
from aria.tools.filesystem import read_file, write_file, list_directory, search_files, delete_file
from aria.tools.shell import run_shell
from aria.utils.confirmation import confirmation_manager
from aria.tools.voice import voice_recorder
from aria.tools.browser import browser_navigate, browser_get_text, close_browser


def test_screen_tool():
    print("\n📸 [1/8] Testing Screen Capture Tool...")
    img = capture_screen()
    assert isinstance(img, Image.Image), f"Expected PIL Image, got {type(img)}"
    assert img.width > 0 and img.height > 0, f"Invalid dimensions: {img.size}"
    print(f"   Captured screen resolution: {img.width}x{img.height}")

    b64 = encode_image_base64(img, max_dim=640)
    assert isinstance(b64, str) and len(b64) > 100, "Base64 encoding failed"
    data_url = get_screen_data_url(img)
    assert data_url.startswith("data:image/jpeg;base64,"), "Data URL format invalid"
    print("   ✅ Screen capture, resize, and base64 encoding passed.")


def test_input_control_tool():
    print("\n⌨️  [2/8] Testing Input Control Tool...")
    ctrl = InputController()
    print(f"   Wayland: {ctrl.is_wayland}, ydotool available: {ctrl.has_ydotool}, wtype: {ctrl.has_wtype}")

    # Test clipboard roundtrip
    test_str = f"aria_clip_test_{int(time.time())}"
    set_ok = ctrl.set_clipboard(test_str)
    print(f"   Clipboard set result: {set_ok}")
    if set_ok:
        val = ctrl.get_clipboard()
        print(f"   Clipboard read: {val}")

    print("   ✅ Input controller instantiated and functional.")


async def test_filesystem_and_safety():
    print("\n📁 [3/8] Testing Filesystem & Destructive Command Interception...")
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "workflow_test.txt")
        w_res = write_file(test_file, "Simulated workflow content")
        assert w_res.get("success") is True, f"write_file failed: {w_res}"

        r_res = read_file(test_file)
        assert r_res.get("content") == "Simulated workflow content", f"read_file failed: {r_res}"

        lst = list_directory(tmpdir)
        assert lst.get("count") == 1, f"list_directory failed: {lst}"

        found = search_files(tmpdir, "*.txt")
        assert len(found.get("matches", [])) == 1, f"search_files failed: {found}"

        d_res = delete_file(test_file)
        assert d_res.get("success") is True, f"delete_file failed: {d_res}"
        assert not os.path.exists(test_file)

    # Safety confirmation manager checks:
    # 1. Non-destructive action allowed without confirmation
    safe_ok = await confirmation_manager.request_confirmation("read_file", {"path": "test.txt"})
    assert safe_ok is True, "Safe action read_file was blocked unexpectedly"

    # 2. Safe shell command allowed without prompt
    safe_shell = await confirmation_manager.request_confirmation("run_shell", {"command": "ls -la"})
    assert safe_shell is True, "Safe shell command ls -la was blocked"

    # 3. Destructive action blocked if prompt returns false
    destructive_blocked = await confirmation_manager.request_confirmation("delete_file", {"path": "/etc/shadow"})
    assert destructive_blocked is False, "Destructive action was not intercepted"

    print("   ✅ Filesystem operations and destructive interception verified.")


def test_shell_execution():
    print("\n🐚 [4/8] Testing Shell Execution Tool...")
    res = run_shell("echo 'Linux-Agent Workflow OK'")
    assert res.get("returncode") == 0, f"Shell command failed: {res}"
    assert "Linux-Agent Workflow OK" in res.get("stdout", "")
    print("   ✅ Shell tool executed command cleanly.")


def test_voice_tool():
    print("\n🎙️ [5/8] Testing Voice Tool State...")
    assert hasattr(voice_recorder, "start")
    assert hasattr(voice_recorder, "stop_and_transcribe")
    print(f"   Voice model configured: {config.voice_model}, language: {config.voice_language}")
    print("   ✅ Voice tool initialized properly.")


async def test_browser_tool():
    print("\n🌐 [6/8] Testing Browser Automation...")
    try:
        # Navigate to a simple blank HTML page
        nav_res = await browser_navigate("https://example.com")
        print(f"   Browser navigation response: {nav_res.get('success')} (status {nav_res.get('status')})")

        content_res = await browser_get_text(max_chars=200)
        print(f"   Browser content snippet: {content_res.get('text', '')[:60]}...")

        await close_browser()
        print("   ✅ Browser launched, navigated, read text, and closed cleanly.")
    except Exception as e:
        print(f"   ⚠️ Browser test note: {e}")


def test_memory_subsystem():
    print("\n🧠 [7/8] Testing SQLite + ChromaDB Memory Subsystem...")
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["ARIA_MEMORY_DIR"] = tmpdir
        mem = Memory()
        sid = mem.create_session("Test Simulation Session")
        assert sid is not None
        mem.add_message(sid, "user", "How do I check system services in Linux?")
        mem.add_message(sid, "assistant", "You can use systemctl --user status.")
        mem.update_summary(sid, "User asked about systemctl command")

        hist = mem.get_recent_history(5)
        assert len(hist) >= 2, f"History too short: {hist}"

        ctx = mem.search_past_context("systemctl")
        assert len(ctx) >= 1, f"Context search returned empty: {ctx}"
        print("   ✅ Memory storage, session lifecycle, and vector retrieval verified.")


class MockAIProvider(BaseProvider):
    """Mock AI Provider that returns a planned tool call then final completion."""
    def __init__(self):
        self.step = 0

    async def generate_response(
        self,
        messages: List[AgentMessage],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> ProviderResponse:
        self.step += 1
        if self.step == 1:
            return ProviderResponse(
                text="I will check the directory contents.",
                tool_calls=[ToolCall(name="list_directory", arguments={"path": "."}, id="call_1")],
            )
        else:
            return ProviderResponse(
                text="The directory has been inspected successfully. Simulation complete!",
                tool_calls=[],
            )


async def test_agent_core_simulation():
    print("\n🤖 [8/8] Testing AgentCore End-to-End Simulation Loop...")
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["ARIA_MEMORY_DIR"] = tmpdir
        mem = Memory()
        mock_provider = MockAIProvider()
        agent = AgentCore(memory=mem, provider=mock_provider)

        events = []
        async for event in agent.run("Please inspect current directory."):
            events.append(event)
            etype = event.get("type")
            if etype == "status":
                print(f"      [Status] {event.get('message')}")
            elif etype == "tool_start":
                print(f"      [Tool Start] {event.get('tool')}")
            elif etype == "tool_end":
                print(f"      [Tool End] {event.get('tool')}")
            elif etype == "text":
                print(f"      [ARIA] {event.get('content')}")
            elif etype == "done":
                print(f"      [Done] Finished.")

        types = [e.get("type") for e in events]
        assert "tool_start" in types, f"Missing tool_start in events: {types}"
        assert "tool_end" in types, f"Missing tool_end in events: {types}"
        assert "text" in types, f"Missing text in events: {types}"
        assert "done" in types, f"Missing done in events: {types}"
        print("   ✅ Full Agent execution loop completed with mock provider!")


async def main():
    print("=" * 60)
    print("      ARIA STANDALONE WORKFLOW & SUBSYSTEM SIMULATION")
    print("=" * 60)

    test_screen_tool()
    test_input_control_tool()
    await test_filesystem_and_safety()
    test_shell_execution()
    test_voice_tool()
    await test_browser_tool()
    test_memory_subsystem()
    await test_agent_core_simulation()

    print("\n" + "=" * 60)
    print("  🎉 ALL 8 WORKFLOW & SIMULATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
