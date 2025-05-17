"""Minimal stub of the openai package for offline testing."""
from types import SimpleNamespace

class _ChatCompletions:
    def create(self, **kwargs):
        # Return an object mimicking the real OpenAI response structure
        content = kwargs.get("messages", [{}])[-1].get("content", "{}")
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.chat = SimpleNamespace(completions=_ChatCompletions())
