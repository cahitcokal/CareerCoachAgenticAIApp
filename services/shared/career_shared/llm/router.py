"""LLM Router: ordered provider/model fallback driven by System Admin config.

Agents never know which vendor they talk to. They call ``invoke_json`` (or
``invoke``) with a prompt; the router loads the agent's runtime configuration
from the system-admin service and walks providers in priority order, then
models in priority order, retrying retryable failures up to ``max_attempts``.
"""
import json
import logging
import time
from dataclasses import dataclass
from typing import Callable

import httpx

from career_shared.config import get_settings
from career_shared.llm.errors import InvalidLLMResponse, LLMError
from career_shared.llm.providers import (
    AnthropicProvider,
    GeminiProvider,
    LLMProvider,
    OpenAICompatibleProvider,
)

logger = logging.getLogger(__name__)

_CONFIG_TTL_SECONDS = 10.0
_config_cache: dict[str, tuple[float, "AgentLLMConfig"]] = {}


@dataclass(frozen=True)
class ProviderEntry:
    provider: str
    models: tuple[str, ...]
    api_key: str | None = None
    base_url: str | None = None


@dataclass(frozen=True)
class AgentLLMConfig:
    agent_name: str
    enabled: bool
    providers: tuple[ProviderEntry, ...]
    max_attempts: int = 3
    max_retry_delay: int = 60
    max_turns: int = 4

    def result_limit(self) -> int:
        return self.max_turns


def _default_agent_config(agent_name: str) -> AgentLLMConfig:
    return AgentLLMConfig(
        agent_name=agent_name,
        enabled=True,
        providers=(ProviderEntry("gemini", ("gemini-2.5-flash", "gemini-3.5-flash")),),
    )


def fetch_agent_config(agent_name: str) -> AgentLLMConfig:
    """Load agent config from system-admin; fall back to env defaults."""
    settings = get_settings()
    now = time.monotonic()
    cached = _config_cache.get(agent_name)
    if cached and now - cached[0] < _CONFIG_TTL_SECONDS:
        return cached[1]
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                f"{settings.system_admin_url}/internal/agents/{agent_name}/config",
                headers={"X-Internal-Key": settings.internal_api_key},
            )
            response.raise_for_status()
            data = response.json()
        config = AgentLLMConfig(
            agent_name=agent_name,
            enabled=bool(data.get("enabled", True)),
            providers=tuple(
                ProviderEntry(
                    provider=str(p["provider"]),
                    models=tuple(p.get("models") or ()),
                    api_key=p.get("api_key"),
                    base_url=p.get("base_url"),
                )
                for p in data.get("providers", [])
            ),
            max_attempts=int(data.get("max_attempts", 3)),
            max_retry_delay=int(data.get("max_retry_delay", 60)),
            max_turns=int(data.get("max_turns", 4)),
        )
    except Exception as exc:
        logger.warning("Agent config fetch failed for %s (%s); using defaults", agent_name, type(exc).__name__)
        config = _default_agent_config(agent_name)
    _config_cache[agent_name] = (now, config)
    return config


def clear_config_cache() -> None:
    _config_cache.clear()


_PROVIDER_DEFAULTS = {
    "gemini": lambda entry: GeminiProvider(api_key=entry.api_key),
    "openai": lambda entry: OpenAICompatibleProvider(
        "openai", entry.base_url or "https://api.openai.com/v1",
        api_key=entry.api_key, api_key_env="OPENAI_API_KEY"),
    "groq": lambda entry: OpenAICompatibleProvider(
        "groq", entry.base_url or "https://api.groq.com/openai/v1",
        api_key=entry.api_key, api_key_env="GROQ_API_KEY"),
    "ollama": lambda entry: OpenAICompatibleProvider(
        "ollama", entry.base_url or "http://localhost:11434/v1",
        api_key=entry.api_key or "ollama", api_key_env="OLLAMA_API_KEY"),
    "anthropic": lambda entry: AnthropicProvider(api_key=entry.api_key),
}


def build_provider(entry: ProviderEntry) -> LLMProvider:
    factory = _PROVIDER_DEFAULTS.get(entry.provider)
    if factory is None:
        raise LLMError(f"Unknown LLM provider: {entry.provider}", retryable=False)
    return factory(entry)


def invoke(
    agent_name: str,
    prompt: str,
    *,
    json_mode: bool = False,
    web_search: bool = False,
    user_id: int | None = None,
    opportunity_id: int | None = None,
    on_attempt: Callable[..., None] | None = None,
) -> str | None:
    """Run a prompt through the configured provider/model fallback chain."""
    config = fetch_agent_config(agent_name)
    if not config.enabled:
        raise LLMError(f"Agent {agent_name} is disabled by system admin", retryable=False)

    last_error: Exception | None = None
    for entry in config.providers:
        provider: LLMProvider | None = None
        try:
            provider = build_provider(entry)
        except Exception as exc:
            logger.warning("[%s] provider init failed: %s", entry.provider, type(exc).__name__)
            last_error = exc
            continue
        if web_search and not provider.supports_web_search:
            logger.info("[%s] skipping provider without web search: %s", agent_name, entry.provider)
            continue
        for model_name in entry.models:
            for attempt in range(1, config.max_attempts + 1):
                if on_attempt:
                    on_attempt(agent_name=agent_name, provider=entry.provider,
                               model=model_name, attempt=attempt)
                try:
                    return provider.generate(
                        model=model_name, prompt=prompt,
                        json_mode=json_mode, web_search=web_search)
                except LLMError as exc:
                    last_error = exc
                    logger.warning("[%s] %s/%s attempt %d failed: %s",
                                   agent_name, entry.provider, model_name, attempt, exc)
                    if exc.retryable and attempt < config.max_attempts:
                        delay = exc.retry_after if exc.retry_after is not None else attempt * 2
                        time.sleep(max(0, min(delay, config.max_retry_delay)))
                        continue
                    break  # next model
                except Exception as exc:  # defensive: providers should raise LLMError
                    last_error = LLMError(str(exc), retryable=False)
                    logger.warning("[%s] %s/%s unexpected error: %s",
                                   agent_name, entry.provider, model_name, type(exc).__name__)
                    break
    raise LLMError(
        f"All LLM providers/models exhausted for {agent_name}: {last_error}",
        retryable=False,
    ) from last_error


def _json_text(text: str, opening: str, closing: str) -> str:
    text = text.strip()
    try:
        json.loads(text)
        return text
    except ValueError:
        pass
    if "```" in text:
        text = text.split("```", 1)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0].strip()
    starts = [index for token in ("[", "{") if (index := text.find(token)) >= 0]
    if starts:
        start = min(starts)
        closing = "]" if text[start] == "[" else "}"
        return text[start:text.rfind(closing) + 1]
    return text


def invoke_json(
    agent_name: str,
    prompt: str,
    *,
    as_list: bool = False,
    web_search: bool = False,
    validator: Callable[[object], None] | None = None,
    user_id: int | None = None,
    opportunity_id: int | None = None,
    on_attempt: Callable[..., None] | None = None,
) -> object:
    """Invoke the router and parse/validate a JSON response.

    Validation failures feed a correction notice back to the same model on the
    next attempt, mirroring the previous monolith behaviour.
    """
    prompt += "\nJSON dışında açıklama veya Markdown yazma. Gereksiz tekrarı kaldır; tüm alanları, somut ayrıntıları ve en/tr karşılıklarını koru."
    config = fetch_agent_config(agent_name)
    if not config.enabled:
        raise LLMError(f"Agent {agent_name} is disabled by system admin", retryable=False)

    current_prompt = prompt
    failure = "Modelden kullanılabilir yanıt alınamadı; sağlayıcı/model erişimini ve logları kontrol edin."
    empty = [] if as_list else {}

    for entry in config.providers:
        provider: LLMProvider | None = None
        try:
            provider = build_provider(entry)
        except Exception as exc:
            logger.warning("[%s] provider init failed: %s", entry.provider, type(exc).__name__)
            continue
        if web_search and not provider.supports_web_search:
            continue
        for model_name in entry.models:
            validation_retries = 0
            for attempt in range(1, config.max_attempts + 1):
                if on_attempt:
                    on_attempt(agent_name=agent_name, provider=entry.provider,
                               model=model_name, attempt=attempt)
                try:
                    text = provider.generate(
                        model=model_name, prompt=current_prompt,
                        json_mode=not web_search, web_search=web_search)
                    if not isinstance(text, str) or not text.strip():
                        raise InvalidLLMResponse("Model kullanılabilir metin yanıtı döndürmedi.")
                    try:
                        parsed_text = _json_text(text, "[" if as_list else "{", "]" if as_list else "}")
                        result = json.loads(parsed_text)
                    except (ValueError, TypeError):
                        raise InvalidLLMResponse(
                            "Yanıt geçerli JSON değil veya boş; yalnızca eksiksiz JSON döndürün.") from None
                    if not isinstance(result, list if as_list else dict):
                        raise InvalidLLMResponse("Yanıtın üst düzey JSON türü şemaya uymuyor.")
                    if validator is not None:
                        validator(result)
                    return result
                except InvalidLLMResponse as exc:
                    failure = str(exc)
                    validation_retries += 1
                    if validation_retries > config.max_attempts:
                        break
                    current_prompt = prompt + "\nDÜZELTME: Önceki yanıt doğrulanamadı. Şu sorunları gidererek planın TAMAMINI yeniden üret; eksik kriterleri gerçek talebe dayanarak yaz, boş veya yer tutucu bırakma. \n" + json.dumps(
                        {"errors": failure}, ensure_ascii=False, separators=(",", ":"))
                    continue
                except LLMError as exc:
                    failure = str(exc)
                    logger.warning("[%s] %s/%s attempt %d failed: %s",
                                   agent_name, entry.provider, model_name, attempt, exc)
                    if exc.retryable and attempt < config.max_attempts:
                        delay = exc.retry_after if exc.retry_after is not None else attempt * 2
                        time.sleep(max(0, min(delay, config.max_retry_delay)))
                        continue
                    break
                except Exception as exc:
                    failure = str(exc)
                    logger.warning("[%s] %s/%s unexpected error: %s",
                                   agent_name, entry.provider, model_name, type(exc).__name__)
                    break
            current_prompt = prompt  # reset correction prompt for next model
    return empty
