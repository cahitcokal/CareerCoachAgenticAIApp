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
os.environ.setdefault("PERSONAL_ADMIN_URL", "http://pa.test")
os.environ.setdefault("SYSTEM_ADMIN_URL", "http://sa.test")
os.environ.setdefault("OPPORTUNITY_SERVICE_URL", "http://os.test")
os.environ.setdefault("SCOUT_AGENT_URL", "http://sc.test")
os.environ.setdefault("RELOCATION_AGENT_URL", "http://ra.test")
os.environ.setdefault("APPLICATION_COACH_AGENT_URL", "http://ca.test")

sys.path.insert(0, _SHARED_DIR)
sys.path.insert(0, _SERVICE_DIR)

import pytest
from fastapi.testclient import TestClient

from career_shared.db import init_db
from career_shared.security import create_access_token


@pytest.fixture(scope="session")
def app():
    import importlib
    import app.main as main_mod
    importlib.reload(main_mod)
    init_db()
    return main_mod.app


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def token():
    return create_access_token(1)


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_headers(token):
    return auth(token)
