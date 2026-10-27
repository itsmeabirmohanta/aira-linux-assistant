import sys
import tempfile
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aria.config import Config
from aria.agent.memory import Memory
from aria.tools.filesystem import read_file, write_file, list_directory, search_files, delete_file
from aria.tools.shell import run_shell


def test_config_defaults():
    cfg = Config()
    assert cfg.hotkey == "ctrl+space"
    assert cfg.provider in ("gemini", "openai", "claude", "ollama")
    assert cfg.display_server in ("wayland", "x11")


def test_filesystem_tools():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.txt")
        # Test write
        w_res = write_file(test_file, "Hello ARIA!")
        assert w_res.get("success") is True

        # Test read
        r_res = read_file(test_file)
        assert r_res.get("content") == "Hello ARIA!"

        # Test list
        l_res = list_directory(tmpdir)
        assert l_res.get("count") == 1

        # Test search
        s_res = search_files(tmpdir, "*.txt")
        assert len(s_res.get("matches", [])) == 1

        # Test delete
        d_res = delete_file(test_file)
        assert d_res.get("success") is True
        assert not os.path.exists(test_file)


def test_shell_tool():
    res = run_shell("echo 'ARIA OK'")
    assert res.get("returncode") == 0
    assert "ARIA OK" in res.get("stdout", "")


def test_memory():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["ARIA_MEMORY_DIR"] = tmpdir
        mem = Memory()
        sid = mem.create_session("Write a Python script")
        assert sid is not None
        mem.add_message(sid, "user", "Can you write a script?")
        mem.add_message(sid, "assistant", "Sure, here it is.")
        mem.update_summary(sid, "Created Python script successfully")

        hist = mem.get_recent_history(5)
        assert len(hist) >= 2
        ctx = mem.search_past_context("script")
        assert len(ctx) >= 1


def test_dpdp_compliance():
    """Verify DPDP Act 2023 / GDPR Data Portability (Export) and Right to Erasure (Purge)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["ARIA_MEMORY_DIR"] = tmpdir
        mem = Memory()
        sid = mem.create_session("DPDP Verification Task")
        mem.add_message(sid, "user", "User test message")
        mem.add_message(sid, "assistant", "Assistant response")
        mem.update_summary(sid, "Summary of task")

        # 1. Right to Data Portability (JSON Export)
        exported = mem.export_personal_data()
        assert len(exported["sessions"]) >= 1
        assert len(exported["messages"]) >= 2
        assert exported["aria_version"] == "2.0"

        # 2. Right to Erasure (Purge)
        purged = mem.purge_all_data()
        assert purged is True
        after = mem.export_personal_data()
        assert len(after["sessions"]) == 0
        assert len(after["messages"]) == 0


if __name__ == "__main__":
    print("🧪 Running ARIA Unit Tests...")
    test_config_defaults()
    print("   ✅ Config defaults verified.")
    test_filesystem_tools()
    print("   ✅ Filesystem tools verified.")
    test_shell_tool()
    print("   ✅ Shell tool verified.")
    test_memory()
    print("   ✅ Memory retrieval verified.")
    test_dpdp_compliance()
    print("   ✅ DPDP Data Portability and Erasure verified.")
    print("🎉 ALL UNIT TESTS PASSED!")
