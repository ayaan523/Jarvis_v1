"""
Tests for Phase 5 OS control shell tool safety gate.
Run from project root: python3 -m unittest tests/test_shell_tool.py -v
"""
import sys
import os
import types
import unittest
from unittest.mock import MagicMock, patch

# --------------------------------------------------------------------------
# Add project root to path first
# --------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --------------------------------------------------------------------------
# Mock ALL heavy / hardware / optional dependencies before any project import.
# This lets tests run on a bare Fedora install without GPU, portaudio, ML models,
# or even a .env file.
# --------------------------------------------------------------------------
_heavy_mods = [
    "dotenv",           # python-dotenv not yet installed
    "sounddevice", "pyaudio", "PyAudio",
    "realtimestt", "RealtimeSTT",
    "torch", "transformers", "safetensors", "accelerate",
    "piper", "piper_tts",
    "kasa",
    "duckduckgo_search",
    "psutil", "pynvml",
    "core.tts", "core.router", "core.llm",
    "PySide6", "PySide6.QtCore", "PySide6.QtWidgets", "PySide6.QtGui",
]
for mod in _heavy_mods:
    sys.modules.setdefault(mod, MagicMock())

# Stub the core package __init__ so it doesn't chain-import everything
if "core" not in sys.modules or not isinstance(sys.modules.get("core"), types.ModuleType):
    _core_stub = types.ModuleType("core")
    _core_stub.__path__ = [os.path.join(PROJECT_ROOT, "core")]
    _core_stub.__package__ = "core"
    sys.modules["core"] = _core_stub

# Build a minimal config stub — we'll patch SHELL_TOOL_ENABLED per-test
import types as _t
_config_stub = _t.ModuleType("config")
_config_stub.SHELL_TOOL_ENABLED = False
_config_stub.GEMINI_MODEL = "gemini-2.5-flash"
_config_stub.OLLAMA_MODEL = "qwen3:1.7b"
_config_stub.OLLAMA_URL = "http://localhost:11434/api"
_config_stub.MAX_HISTORY = 20
_config_stub.GRAY = ""
_config_stub.RESET = ""
_config_stub.CYAN = ""
_config_stub.GREEN = ""
sys.modules["config"] = _config_stub

# --------------------------------------------------------------------------
# Now safe to load FunctionExecutor directly via importlib
# --------------------------------------------------------------------------
import importlib.util

_fe_spec = importlib.util.spec_from_file_location(
    "core.function_executor",
    os.path.join(PROJECT_ROOT, "core", "function_executor.py"),
)
_fe_mod = importlib.util.module_from_spec(_fe_spec)
sys.modules["core.function_executor"] = _fe_mod
_fe_spec.loader.exec_module(_fe_mod)
FunctionExecutor = _fe_mod.FunctionExecutor


# ==========================================================================
class TestShellToolDenylist(unittest.TestCase):
    """Phase 5 requirement: denylist MUST block every destructive pattern."""

    def setUp(self):
        self.executor = FunctionExecutor()

    def _run(self, command: str, enabled: bool = True) -> dict:
        sys.modules["config"].SHELL_TOOL_ENABLED = enabled
        return self.executor.execute(
            "run_shell_command",
            {"command": command, "reason": "safety-gate test"},
        )

    # --- disabled-by-default ---
    def test_disabled_by_default(self):
        result = self._run("echo hello", enabled=False)
        self.assertFalse(result["success"])
        self.assertIn("disabled in config", result["message"])

    # --- each denylist pattern must block ---
    def _assert_blocked(self, command: str):
        result = self._run(command, enabled=True)
        self.assertFalse(
            result["success"],
            f"SAFETY FAILURE — command was NOT blocked: {command!r}",
        )
        self.assertIn(
            "DANGEROUS COMMAND BLOCKED",
            result["message"],
            f"Wrong message for blocked command: {command!r}",
        )
        self.assertTrue(
            result.get("data", {}).get("requires_confirmation"),
            f"Missing requires_confirmation flag for: {command!r}",
        )

    def test_rm_rf(self):        self._assert_blocked("rm -rf /")
    def test_rm_rf_home(self):   self._assert_blocked("rm -rf /home/user/data")
    def test_dnf_remove(self):   self._assert_blocked("sudo dnf remove python3")
    def test_mkfs(self):         self._assert_blocked("mkfs.ext4 /dev/sda1")
    def test_redirect_dev(self): self._assert_blocked("echo 0 > /dev/sda")
    def test_dd_if(self):        self._assert_blocked("dd if=/dev/zero of=/dev/sda bs=1M")
    def test_fork_bomb(self):    self._assert_blocked(":(){ :|:& };:")
    def test_sudo_plain(self):   self._assert_blocked("sudo systemctl restart sshd")
    def test_su(self):           self._assert_blocked("su -c 'rm /etc/shadow'")
    def test_redirect_etc(self): self._assert_blocked("echo 'root::0:0:root:/root:/bin/bash' > /etc/passwd")
    def test_redirect_bin(self): self._assert_blocked("echo evil > /bin/sh")
    def test_mv_root(self):      self._assert_blocked("mv / /trash")
    def test_chown(self):        self._assert_blocked("chown root:root /etc")
    def test_chmod_R(self):      self._assert_blocked("chmod -R 777 /usr")

    @patch("core.function_executor.subprocess.run")
    def test_confirmation_executes_only_the_pending_command(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = "ok"
        run.return_value.stderr = ""
        self._run("sudo echo guarded", enabled=True)
        result = self.executor.confirm_pending_shell_command("no")
        self.assertFalse(result["success"])
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()


def tearDownModule():
    for module_name in ("config", "core.function_executor", "core"):
        sys.modules.pop(module_name, None)
