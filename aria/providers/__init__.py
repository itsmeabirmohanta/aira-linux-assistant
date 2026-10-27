"""
Provider factory for ARIA.
"""

from aria.config import config
from aria.providers.base import BaseProvider
from aria.providers.gemini import GeminiProvider
from aria.providers.openai_p import OpenAIProvider
from aria.providers.claude import ClaudeProvider
from aria.providers.ollama_p import OllamaProvider

_active_provider: BaseProvider = None


def get_provider() -> BaseProvider:
    global _active_provider
    if _active_provider is not None:
        return _active_provider

    p = config.provider.lower()
    if p == "gemini":
        _active_provider = GeminiProvider()
    elif p in ("openai", "gpt-4o", "gpt4o"):
        _active_provider = OpenAIProvider()
    elif p in ("claude", "anthropic"):
        _active_provider = ClaudeProvider()
    elif p == "ollama":
        _active_provider = OllamaProvider()
    else:
        # Default to Gemini
        _active_provider = GeminiProvider()

    return _active_provider
