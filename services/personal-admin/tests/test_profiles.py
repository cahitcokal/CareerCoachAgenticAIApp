from conftest import auth


def _profile_payload(name="Test Profile"):
    return {"name": name, "title": "Engineer", "experience": "5 years"}


def test_profile_crud_and_soft_delete(client, auth_headers):
    resp = client.post("/profiles", headers=auth_headers, json=_profile_payload())
    assert resp.status_code == 201
    profile = resp.json()
    assert profile["is_active"] is True

    listed = client.get("/profiles", headers=auth_headers).json()
    assert any(p["id"] == profile["id"] for p in listed)

    # Soft delete
    assert client.delete(f"/profiles/{profile['id']}", headers=auth_headers).status_code == 204
    listed = client.get("/profiles", headers=auth_headers).json()
    assert all(p["id"] != profile["id"] for p in listed)

    # Still visible with include_deleted
    all_profiles = client.get("/profiles?include_deleted=true", headers=auth_headers).json()
    deleted = next(p for p in all_profiles if p["id"] == profile["id"])
    assert deleted["is_active"] is False
    assert deleted["deleted_at"] is not None

    # Restore
    restored = client.post(f"/profiles/{profile['id']}/restore", headers=auth_headers)
    assert restored.status_code == 200
    assert restored.json()["is_active"] is True
    assert restored.json()["deleted_at"] is None


def test_profile_isolation_between_users(client, auth_headers):
    other_token = __import__("career_shared.security", fromlist=["create_access_token"]).create_access_token(999)
    resp = client.post("/profiles", headers=auth(other_token), json=_profile_payload("Other"))
    assert resp.status_code == 201
    # User 1 cannot see user 999's profile
    assert client.get(f"/profiles/{resp.json()['id']}", headers=auth_headers).status_code == 404


def test_target_lists_crud(client, auth_headers):
    resp = client.post("/target-countries", headers=auth_headers,
                       json={"name": "Germany", "notes": "EU"})
    assert resp.status_code == 201
    item = resp.json()
    listed = client.get("/target-countries", headers=auth_headers).json()
    assert any(i["id"] == item["id"] for i in listed)
    assert client.delete(f"/target-countries/{item['id']}", headers=auth_headers).status_code == 204


def test_preferences_roundtrip(client, auth_headers):
    resp = client.put("/preferences", headers=auth_headers, json={"language": "tr"})
    assert resp.status_code == 200
    assert resp.json()["language"] == "tr"
    assert client.get("/preferences", headers=auth_headers).json()["language"] == "tr"


def test_seed_defaults(client):
    resp = client.post("/internal/users/42/seed-defaults",
                       headers={"X-Internal-Key": "test-internal"})
    assert resp.status_code == 201
    countries = client.get("/internal/targets", params={"user_id": 42},
                           headers={"X-Internal-Key": "test-internal"}).json()
    assert len(countries["countries"]) > 0
    assert len(countries["roles"]) > 0
    assert len(countries["career_sites"]) > 0
