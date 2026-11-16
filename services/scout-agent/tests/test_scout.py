import pytest


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            raise httpx.HTTPStatusError("err", request=None, response=None)


class FakeOpportunities:
    """Stands in for career_shared.client.ServiceClient on opportunity-service."""

    def __init__(self):
        self.runs = {}
        self.created = []
        self._next_id = 1

    def post(self, path, **kwargs):
        if path == "/internal/agent-runs":
            meta = (kwargs.get("json") or {}).get("meta") or {}
            uid = meta.get("user_id")
            for run in self.runs.values():
                if run["status"] == "running" and run["agent"] == "scout" and run["user"] == uid:
                    return FakeResponse(409, {"detail": "already running"})
            run_id = self._next_id
            self._next_id += 1
            self.runs[run_id] = {"agent": "scout", "user": uid, "status": "running"}
            return FakeResponse(201, {"id": run_id, "status": "running"})
        if path.endswith("/finish"):
            run_id = int(path.split("/")[-2])
            self.runs[run_id]["status"] = (kwargs.get("json") or {}).get("status", "success")
            return FakeResponse(200, {"id": run_id})
        if path == "/internal/opportunities":
            self.created.append(kwargs.get("json"))
            return FakeResponse(201, {"id": len(self.created)})
        if path == "/internal/audit-logs":
            return FakeResponse(201, {"id": 1})
        return FakeResponse(404)

    def get(self, path, **kwargs):
        if path == "/internal/agent-runs/ongoing":
            agent = (kwargs.get("params") or {}).get("agent_name")
            uid = (kwargs.get("params") or {}).get("user_id")
            return FakeResponse(200, [
                {"id": rid, "started_at": "2024-01-01T00:00:00"}
                for rid, r in self.runs.items()
                if r["agent"] == agent and r["user"] == uid and r["status"] == "running"
            ])
        return FakeResponse(404)


class FakePersonalAdmin:
    def get(self, path, **kwargs):
        if path == "/internal/profiles":
            return FakeResponse(200, [{"id": 7, "name": "Test", "title": "Dev"}])
        if path.startswith("/internal/profiles/"):
            return FakeResponse(200, {"id": 7, "name": "Test", "title": "Dev"})
        if path == "/internal/targets":
            return FakeResponse(200, {"countries": [{"name": "Germany"}],
                                      "roles": [{"name": "Engineer"}],
                                      "career_sites": [{"name": "LinkedIn"}]})
        return FakeResponse(404)


@pytest.fixture()
def fakes(monkeypatch):
    import app.main as main_mod
    opp = FakeOpportunities()
    pa = FakePersonalAdmin()
    monkeypatch.setattr(main_mod, "_opportunities", opp)
    monkeypatch.setattr(main_mod, "_personal_admin", pa)
    # Keep runs "running" — background tasks are no-ops in unit tests.
    monkeypatch.setattr(main_mod, "_run_search", lambda *a, **k: None)
    monkeypatch.setattr(main_mod, "_run_url_analysis", lambda *a, **k: None)
    return opp, pa


def test_search_returns_202_and_registers_run(client, auth_headers, fakes):
    resp = client.post("/search", headers=auth_headers, json={
        "query": "backend engineer", "max_results": 5})
    assert resp.status_code == 202
    assert resp.json()["status"] == "running"


def test_second_search_rejected_while_running(client, auth_headers, fakes):
    opp, _ = fakes
    client.post("/search", headers=auth_headers, json={"query": "x"})
    # run still running in fake registry
    resp = client.post("/search", headers=auth_headers, json={"query": "y"})
    assert resp.status_code == 409


def test_analyze_url_202(client, auth_headers, fakes):
    resp = client.post("/analyze-url", headers=auth_headers,
                       json={"url": "https://jobs.example.com/123"})
    assert resp.status_code == 202


def test_runs_endpoint(client, auth_headers, fakes):
    client.post("/search", headers=auth_headers, json={"query": "x"})
    runs = client.get("/runs", headers=auth_headers).json()
    assert isinstance(runs, list)
