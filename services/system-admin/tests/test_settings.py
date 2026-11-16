import pytest
from fastapi.testclient import TestClient


def test_seeded_defaults(client, admin_headers):
    # Startup seeding runs via TestClient context manager.
    with TestClient(client.app) as c:
        langs = c.get("/languages", headers=admin_headers).json()
        # _require_admin is bypassed in tests
        assert len(langs) >= 2
        assert any(l["is_default"] for l in langs)


def test_language_enable_disable_rules(client, admin_headers):
    with TestClient(client.app) as c:
        headers = admin_headers
        langs = c.get("/languages", headers=headers).json()
        codes = [l["code"] for l in langs]
        assert "tr" in codes and "en" in codes

        # Disabling all-but-one is fine; disabling the last enabled must fail.
        for lang in langs:
            if lang["code"] != "tr":
                resp = c.put(f"/languages/{lang['code']}", headers=headers,
                             json={**lang, "enabled": False})
                assert resp.status_code == 200
        resp = c.put("/languages/tr", headers=headers,
                     json={"code": "tr", "name": "Türkçe", "enabled": False,
                           "is_default": True, "sort_order": 0})
        assert resp.status_code == 400


def test_provider_and_model_management(client, admin_headers):
    with TestClient(client.app) as c:
        headers = admin_headers
        providers = c.get("/providers", headers=headers).json()
        names = {p["provider"] for p in providers}
        assert {"gemini", "openai", "anthropic", "groq", "ollama"} <= names

        resp = c.put("/providers/gemini", headers=headers, json={
            "display_name": "Gemini", "api_key": "test-key-123",
            "priority": 1, "enabled": True})
        assert resp.status_code == 200
        assert resp.json()["has_api_key"] is True
        assert "api_key" not in resp.json() or resp.json().get("api_key") is None

        resp = c.post("/providers/gemini/models", headers=headers,
                      json={"model": "gemini-2.5-flash", "priority": 1})
        assert resp.status_code == 201
        model_id = resp.json()["id"]
        resp = c.patch(f"/providers/gemini/models/{model_id}", headers=headers,
                       json={"enabled": False})
        assert resp.json()["enabled"] is False


def test_agent_settings_and_internal_config(client, admin_headers):
    with TestClient(client.app) as c:
        headers = admin_headers
        agents = c.get("/agents", headers=headers).json()
        names = {a["agent_name"] for a in agents}
        assert {"scout", "relocation", "application_coach"} <= names

        scout = next(a for a in agents if a["agent_name"] == "scout")
        resp = c.put("/agents/scout", headers=headers, json={
            "enabled": False, "provider_order": ["gemini"],
            "max_attempts": 5, "max_retry_delay": 30, "max_turns": 10})
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

        # Internal config used by the LLM router.
        internal = c.get("/internal/agents/scout/config",
                         headers={"X-Internal-Key": "test-internal"})
        assert internal.status_code == 200
        data = internal.json()
        assert data["enabled"] is False
        assert data["max_attempts"] == 5
        assert data["providers"][0]["provider"] == "gemini"


def test_internal_languages_public(client):
    with TestClient(client.app) as c:
        pub = c.get("/languages/public")
        assert pub.status_code == 200
        assert pub.json()["default"] is not None
