import os
import sys
import tempfile

_SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SHARED_DIR = os.path.join(os.path.dirname(_SERVICE_DIR), "shared")

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}")
os.environ.setdefault("JWT_SECRET", "test-secret-key-32-chars-minimum!!")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("USER_MANAGEMENT_URL", "http://um.test")
os.environ.setdefault("SETTINGS_ENCRYPTION_KEY", "49me8RtcZy1cEWhWr11FiMaGQNumhItJ6bflH7SeRW0=")

sys.path.insert(0, _SHARED_DIR)
sys.path.insert(0, _SERVICE_DIR)

import pytest
from fastapi.testclient import TestClient

from career_shared.db import init_db


@pytest.fixture(scope="session")
def app():
    import app.main as main_mod
    init_db()
    return main_mod.app


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture(autouse=True)
def _bypass_admin_check(monkeypatch):
    """Admin role lives in user-management; stub the HTTP check in unit tests."""
    import app.main as main_mod
    monkeypatch.setattr(main_mod, "_require_admin", lambda user_id, db: None)


@pytest.fixture()
def admin_headers():
    from career_shared.security import create_access_token
    return {"Authorization": f"Bearer {create_access_token(1)}"}
