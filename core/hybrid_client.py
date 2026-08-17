"""Compatibility streaming API backed by the selected LLM backend."""

import logging

from core.backends import GeminiBackend, OllamaBackend, select_backend

logger = logging.getLogger(__name__)


def stream_chat_response(messages, enable_thinking=False):
    backend = select_backend()
    try:
        yield from backend.stream(messages, enable_thinking)
    except Exception as error:
        if isinstance(backend, GeminiBackend):
            logger.warning("Gemini failed; retrying this turn with Ollama: %s", error)
            yield "[Gemini unavailable; using local Ollama.] ", None
            yield from OllamaBackend().stream(messages, enable_thinking)
            return
        raise


def generate_chat_response(messages, enable_thinking=False, temperature=None):
    backend = select_backend()
    try:
        return backend.generate(messages, temperature=temperature)
    except Exception as error:
        if isinstance(backend, GeminiBackend):
            logger.warning("Gemini failed; retrying this turn with Ollama: %s", error)
            return OllamaBackend().generate(messages, temperature=temperature)
        raise
