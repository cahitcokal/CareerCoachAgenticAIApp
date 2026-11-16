import jwt
import pytest

from career_shared.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from career_shared.llm.errors import LLMError, classify_http_error
from career_shared.llm.router import AgentLLMConfig, ProviderEntry


def test_password_hash_roundtrip():
    hashed = get_password_hash("super-secret-123")
    assert hashed != "super-secret-123"
    assert verify_password("super-secret-123", hashed)
    assert not verify_password("wrong", hashed)
    assert not verify_password("x", "")


def test_jwt_roundtrip():
    token = create_access_token(42, {"role": "admin"})
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "admin"


def test_jwt_invalid_signature():
    token = create_access_token(1)
    with pytest.raises(jwt.PyJWTError):
        jwt.decode(token, "wrong-secret", algorithms=["HS256"])


def test_llm_error_classification():
    class FakeExc(Exception):
        code = 429
    err = classify_http_error(FakeExc("rate limited"))
    assert isinstance(err, LLMError)
    assert err.retryable


def test_agent_config_dataclass():
    cfg = AgentLLMConfig(agent_name="scout", enabled=True,
                         providers=(ProviderEntry("gemini", ("m1", "m2")),))
    assert cfg.result_limit() == 4
    assert cfg.providers[0].models == ("m1", "m2")
