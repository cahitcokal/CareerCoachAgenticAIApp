import pytest


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        pass


class FakeOpportunities:
    def __init__(self):
        self.runs = {}
        self.created_steps = []
        self.deleted_steps = False
        self._next_id = 1
        self.opportunities = {1: {"id": 1, "user_id": 1, "title": "Dev", "profile_id": 7}}

    def post(self, path, **kwargs):
        if path == "/internal/agent-runs":
            run_id = self._next_id; self._next_id += 1
            self.runs[run_id] = "running"
            return FakeResponse(201, {"id": run_id, "status": "running"})
        if path.endswith("/finish"):
            self.runs[int(path.split("/")[-2])] = "success"
            return FakeResponse(200, {})
        if path.endswith("/steps"):
            self.created_steps.extend(kwargs.get("json") or [])
            return FakeResponse(201, [])
        if path == "/internal/audit-logs":
            return FakeResponse(201, {"id": 1})
        return FakeResponse(404)

    def get(self, path, **kwargs):
        if path == "/internal/opportunities":
            return FakeResponse(200, list(self.opportunities.values()))
        if path.startswith("/internal/opportunities/"):
            oid = int(path.rsplit("/", 1)[-1])
            if oid in self.opportunities:
                return FakeResponse(200, self.opportunities[oid])
        if path == "/internal/agent-runs/ongoing":
            return FakeResponse(200, [])
        return FakeResponse(404)

    def patch(self, path, **kwargs):
        oid = int(path.rsplit("/", 1)[-1])
        if oid in self.opportunities:
            self.opportunities[oid].update(kwargs.get("json") or {})
        return FakeResponse(200, {})

    def delete(self, path, **kwargs):
        if path.endswith("/steps"):
            self.deleted_steps = True
        return FakeResponse(200, {})


class FakePersonalAdmin:
    def get(self, path, **kwargs):
        if path.startswith("/internal/profiles"):
            return FakeResponse(200, {"id": 7, "name": "Test"})
        return FakeResponse(404)


@pytest.fixture()
def fakes(monkeypatch):
    import app.main as main_mod
    opp = FakeOpportunities()
    monkeypatch.setattr(main_mod, "_opportunities", opp)
    monkeypatch.setattr(main_mod, "_personal_admin", FakePersonalAdmin())
    return opp


def test_application_steps_202(client, auth_headers, fakes, monkeypatch):
    import app.main as main_mod
    monkeypatch.setattr(main_mod, "invoke_json", lambda *a, **k: [
        {"step_order": 1, "title": "Tailor CV", "document_draft": "draft"},
        {"step_order": 2, "title": "Apply", "description": "submit"},
    ])
    resp = client.post("/application-steps", headers=auth_headers,
                       json={"opportunity_id": 1})
    assert resp.status_code == 202


def test_application_steps_404_for_foreign_opportunity(client, auth_headers, fakes):
    resp = client.post("/application-steps", headers=auth_headers,
                       json={"opportunity_id": 999})
    assert resp.status_code == 404


def test_runs_endpoint(client, auth_headers, fakes):
    assert client.get("/runs", headers=auth_headers).json() == []
