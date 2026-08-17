import unittest
import sys
import os
from types import SimpleNamespace
from unittest.mock import Mock, patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if "config" in sys.modules and not hasattr(sys.modules["config"], "ULTRA_LIGHT_MODE"):
    del sys.modules["config"]

def backend_modules():
    if "config" in sys.modules and not hasattr(sys.modules["config"], "ULTRA_LIGHT_MODE"):
        del sys.modules["config"]
    import config
    from core.backends import OllamaBackend
    from core.gemini_client import generate_with_tools
    return config.FUNCTIONS, OllamaBackend, generate_with_tools


class TestBackendTools(unittest.TestCase):
    def test_gemini_tool_round_trip(self):
        functions, _, generate_with_tools = backend_modules()
        model_content = SimpleNamespace()
        first = SimpleNamespace(
            function_calls=[SimpleNamespace(name="list_windows", args={})],
            candidates=[SimpleNamespace(content=model_content)],
            text="",
        )
        final = SimpleNamespace(function_calls=[], text="No windows available.")
        client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **_: first))
        client.models.generate_content = Mock(side_effect=[first, final])
        executed = []
        with patch("core.gemini_client.get_client", return_value=client), \
             patch("core.gemini_client.types.Content", side_effect=lambda **_: SimpleNamespace()), \
             patch("core.gemini_client.types.Part.from_function_response", return_value=SimpleNamespace()):
            response = generate_with_tools(
                "gemini-2.5-flash", [{"role": "user", "content": "list windows"}], functions,
                lambda name, args: executed.append((name, args)) or {"success": True},
            )
        self.assertEqual(response, "No windows available.")
        self.assertEqual(executed, [("list_windows", {})])

    def test_ollama_tool_round_trip(self):
        functions, OllamaBackend, _ = backend_modules()
        first = SimpleNamespace(raise_for_status=lambda: None, json=lambda: {
            "message": {"content": "", "tool_calls": [{"function": {"name": "list_windows", "arguments": {}}}]}
        })
        final = SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"message": {"content": "No windows available."}})
        executed = []
        with patch.object(OllamaBackend, "_ensure_running"), patch("core.backends.requests.post", side_effect=[first, final]) as post:
            response = OllamaBackend().generate(
                [{"role": "user", "content": "list windows"}], functions,
                lambda name, args: executed.append((name, args)) or {"success": True},
            )
        self.assertEqual(response, "No windows available.")
        self.assertEqual(executed, [("list_windows", {})])
        self.assertEqual(post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
