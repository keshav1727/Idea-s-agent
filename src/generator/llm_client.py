"""Pluggable LLM backend: Ollama (default, free) or OpenAI-compatible API."""

from __future__ import annotations
import os
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract interface for LLM backends."""

    @abstractmethod
    def generate(self, prompt: str, system: str = "") -> str:
        """Send a prompt and return the raw text response."""
        ...


class OllamaClient(LLMClient):
    """Local LLM via Ollama — free, no API key needed."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3")

    def generate(self, prompt: str, system: str = "") -> str:
        import ollama
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = ollama.chat(model=self.model, messages=messages)
        return response["message"]["content"]


class OpenAIClient(LLMClient):
    """OpenAI-compatible API (works with OpenAI, Together, Groq, etc.)."""

    def __init__(self):
        import openai
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=4000,
        )
        return response.choices[0].message.content or ""
