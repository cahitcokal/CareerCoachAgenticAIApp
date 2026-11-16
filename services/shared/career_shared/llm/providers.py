"""LLM provider implementations.

Every provider exposes the same minimal surface so the router can fall back
across vendors: ``generate(model, prompt, json_mode, web_search)``.
"""
import os
from typing import Protocol

import httpx

from career_shared.llm.errors import LLMError, classify_http_error


class LLMProvider(Protocol):
    name: str
    supports_web_search: bool

    def generate(self, *, model: str, prompt: str, json_mode: bool = False,
                 web_search: bool = False) -> str | None: ...


def extract_gemini_text(response) -> str | None:
    if not response.candidates or not response.candidates[0].content:
        return None
    parts = response.candidates[0].content.parts or []
    texts = [part.text for part in parts if isinstance(part.text, str) and not part.thought]
    return "".join(texts) if texts else None


class GeminiProvider:
    name = "gemini"
    supports_web_search = True

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        from google import genai
        self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))

    def generate(self, *, model, prompt, json_mode=False, web_search=False):
        from google.genai import types
        options = {}
        if json_mode:
            options["response_mime_type"] = "application/json"
        if web_search:
            options["tools"] = [{"google_search": {}}]
        try:
            response = self.client.models.generate_content(
                model=model, contents=prompt, config=types.GenerateContentConfig(**options))
            return extract_gemini_text(response)
        except Exception as exc:
            raise classify_http_error(exc) from exc


class OpenAICompatibleProvider:
    """Covers OpenAI, Groq and Ollama — all expose /chat/completions."""

    supports_web_search = False

    def __init__(self, name: str, base_url: str, api_key: str | None = None,
                 api_key_env: str | None = None, timeout: float = 120.0):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key if api_key is not None else os.getenv(api_key_env or "", "")
        self.timeout = timeout

    def generate(self, *, model, prompt, json_mode=False, web_search=False):
        if web_search:
            raise LLMError(f"{self.name} does not support web search", retryable=False)
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/chat/completions",
                                       json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            raise classify_http_error(exc) from exc
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMError(str(exc), retryable=isinstance(exc, httpx.TransportError)) from exc


class AnthropicProvider:
    name = "anthropic"
    supports_web_search = False

    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    def __init__(self, api_key: str | None = None, timeout: float = 120.0):
        self.api_key = api_key if api_key is not None else os.getenv("ANTHROPIC_API_KEY", "")
        self.timeout = timeout

    def generate(self, *, model, prompt, json_mode=False, web_search=False):
        if web_search:
            raise LLMError("anthropic does not support web search", retryable=False)
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 8192,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.API_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
            return "".join(block.get("text", "") for block in data.get("content", []))
        except httpx.HTTPStatusError as exc:
            raise classify_http_error(exc) from exc
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMError(str(exc), retryable=isinstance(exc, httpx.TransportError)) from exc
