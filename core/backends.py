"""Small, shared Gemini/Ollama backend selection layer."""

import json
import logging
import shutil
import socket
import subprocess
import time
from typing import Iterator

import requests

from config import GEMINI_MODEL, OLLAMA_MODEL, OLLAMA_URL, ULTRA_LIGHT_MODE
from core.gemini_client import generate_chat_response as gemini_generate
from core.gemini_client import generate_with_tools as gemini_generate_with_tools
from core.gemini_client import stream_chat_response as gemini_stream

logger = logging.getLogger(__name__)
_cached_backend = None
_cache_expires_at = 0.0


def translate_tools(tools, backend):
    """Translate the project tool schema for either supported API."""
    declarations = [tool["function"] for tool in tools if tool.get("type") == "function"]
    if backend == "gemini":
        return [{"function_declarations": declarations}]
    return [{"type": "function", "function": declaration} for declaration in declarations]


class GeminiBackend:
    name = "Gemini Flash"

    def stream(self, messages, enable_thinking=False) -> Iterator[tuple[str, None]]:
        for text in gemini_stream(GEMINI_MODEL, messages):
            if text:
                yield text, None

    def generate(self, messages, tools=None, execute_tool=None, temperature=None):
        if tools and execute_tool:
            return gemini_generate_with_tools(GEMINI_MODEL, messages, tools, execute_tool, temperature=temperature)
        return gemini_generate(GEMINI_MODEL, messages, temperature=temperature)


class OllamaBackend:
    name = "Ollama"

    def _ensure_running(self):
        try:
            requests.get(OLLAMA_URL.rsplit("/api", 1)[0], timeout=0.5)
            return
        except requests.RequestException:
            pass
        if not ULTRA_LIGHT_MODE and shutil.which("ollama"):
            logger.info("Starting Ollama for offline fallback.")
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
            for _ in range(10):
                time.sleep(0.2)
                try:
                    requests.get(OLLAMA_URL.rsplit("/api", 1)[0], timeout=0.2)
                    return
                except requests.RequestException:
                    continue
        hint = "Start Ollama with `ollama serve`" if ULTRA_LIGHT_MODE else "Install/start Ollama"
        raise RuntimeError(f"Gemini is unreachable and Ollama is unavailable. {hint} or reconnect.")

    def stream(self, messages, enable_thinking=False):
        self._ensure_running()
        payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": True,
                   "think": enable_thinking, "keep_alive": "5m"}
        with requests.post(f"{OLLAMA_URL}/chat", json=payload, stream=True, timeout=120) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    message = json.loads(line).get("message", {})
                    yield message.get("content"), message.get("thinking")

    def generate(self, messages, tools=None, execute_tool=None, temperature=None):
        self._ensure_running()
        payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": False,
                   "tools": translate_tools(tools or [], "ollama")}
        if temperature is not None:
            payload["options"] = {"temperature": temperature}
        response = requests.post(f"{OLLAMA_URL}/chat", json=payload, timeout=120)
        response.raise_for_status()
        message = response.json().get("message", {})
        calls = message.get("tool_calls", [])
        if not calls or not execute_tool:
            return message.get("content", "")
        follow_up = list(messages) + [{"role": "assistant", "content": message.get("content", ""), "tool_calls": calls}]
        for call in calls:
            function = call.get("function", {})
            result = execute_tool(function.get("name", ""), function.get("arguments", {}))
            follow_up.append({"role": "tool", "tool_name": function.get("name", ""),
                              "content": json.dumps(result)})
        payload["messages"] = follow_up
        response = requests.post(f"{OLLAMA_URL}/chat", json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")


def _gemini_reachable():
    try:
        with socket.create_connection(("generativelanguage.googleapis.com", 443), timeout=0.3):
            return True
    except OSError:
        return False


def select_backend(force_refresh=False):
    """Return a cached backend after checking the actual Gemini API host."""
    global _cached_backend, _cache_expires_at
    now = time.monotonic()
    if not force_refresh and _cached_backend and now < _cache_expires_at:
        return _cached_backend
    _cached_backend = GeminiBackend() if _gemini_reachable() else OllamaBackend()
    _cache_expires_at = now + 30
    logger.info("Active backend: %s", _cached_backend.name)
    return _cached_backend
