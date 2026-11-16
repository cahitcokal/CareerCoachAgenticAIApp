"""Normalized LLM errors shared by providers and the router."""
import re


class LLMError(Exception):
    def __init__(self, message, *, retryable=False, retry_after=None):
        super().__init__(message)
        self.retryable = retryable
        self.retry_after = retry_after


class InvalidLLMResponse(ValueError):
    """Safe validation feedback; never contains provider credentials or raw inputs."""


def classify_http_error(exc, *, retryable_codes=(429, 500, 502, 503, 504)) -> LLMError:
    message = str(exc)
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    retryable = code in retryable_codes or any(
        marker in message for marker in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded")
    )
    delay = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+)", message)
    return LLMError(message, retryable=retryable, retry_after=int(delay.group(1)) if delay else None)
