from conftest import auth


def _opp(title="Software Engineer", **kw):
    return {"title": title, "company": "Acme", "location": "Berlin",
            "url": "https://example.com/job/1", "status": "new", **kw}


def test_opportunity_lifecycle(client, auth_headers):
    resp = client.post("/opportunities", headers=auth_headers, json=_opp())
    assert resp.status_code == 201
    opp = resp.json()
    assert opp["status"] == "new"

    listed = client.get("/opportunities", headers=auth_headers).json()
    assert any(o["id"] == opp["id"] for o in listed)

    resp = client.patch(f"/opportunities/{opp['id']}", headers=auth_headers,
                        json={"status": "active", "match_score": 87})
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"

    # Invalid status rejected
    resp = client.patch(f"/opportunities/{opp['id']}", headers=auth_headers,
                        json={"status": "bogus"})
    assert resp.status_code == 400

    assert client.delete(f"/opportunities/{opp['id']}", headers=auth_headers).status_code == 204


def test_opportunity_filters(client, auth_headers):
    client.post("/opportunities", headers=auth_headers,
                json=_opp("Backend Dev", company="Acme", match_score=90))
    client.post("/opportunities", headers=auth_headers,
                json=_opp("Frontend Dev", company="Beta", match_score=40, status="active"))

    all_opps = client.get("/opportunities", headers=auth_headers).json()
    assert len(all_opps) >= 2

    by_company = client.get("/opportunities?company=acme", headers=auth_headers).json()
    assert all("acme" in (o["company"] or "").lower() for o in by_company)

    by_score = client.get("/opportunities?min_score=80", headers=auth_headers).json()
    assert all((o["match_score"] or 0) >= 80 for o in by_score)

    by_status = client.get("/opportunities?status=active", headers=auth_headers).json()
    assert all(o["status"] == "active" for o in by_status)


def test_steps_crud(client, auth_headers):
    opp = client.post("/opportunities", headers=auth_headers, json=_opp()).json()
    step = client.post(f"/opportunities/{opp['id']}/steps", headers=auth_headers,
                       json={"step_order": 1, "title": "Tailor CV",
                             "document_draft": "# Cover letter draft"}).json()
    assert step["title"] == "Tailor CV"

    patched = client.patch(f"/opportunities/{opp['id']}/steps/{step['id']}",
                           headers=auth_headers, json={"completed": True})
    assert patched.json()["completed"] is True

    detail = client.get(f"/opportunities/{opp['id']}", headers=auth_headers).json()
    assert len(detail["steps"]) == 1


def test_agent_run_registry(client, auth_headers):
    internal = {"X-Internal-Key": "test-internal"}
    resp = client.post("/internal/agent-runs", headers=internal, json={
        "agent_name": "scout", "meta": {"user_id": 1}})
    assert resp.status_code == 201
    run_id = resp.json()["id"]

    # Duplicate ongoing run rejected
    resp = client.post("/internal/agent-runs", headers=internal, json={
        "agent_name": "scout", "meta": {"user_id": 1}})
    assert resp.status_code == 409

    # Ongoing list shows the run for the user-facing endpoint
    runs = client.get("/agent-runs", headers=auth_headers).json()
    assert any(r["id"] == run_id and r["status"] == "running" for r in runs)

    client.post(f"/internal/agent-runs/{run_id}/finish", headers=internal,
                json={"status": "success"})
    runs = client.get("/agent-runs", headers=auth_headers).json()
    assert any(r["id"] == run_id and r["status"] == "success" for r in runs)


def test_audit_log_internal(client):
    internal = {"X-Internal-Key": "test-internal"}
    resp = client.post("/internal/audit-logs", headers=internal, json={
        "user_id": 1, "agent_name": "scout", "provider": "gemini",
        "model_name": "gemini-2.5-flash", "prompt_input": "prompt",
        "response_output": "{}", "status": "success"})
    assert resp.status_code == 201
    logs = client.get("/internal/audit-logs", headers=internal,
                      params={"agent_name": "scout"}).json()
    assert len(logs) >= 1
