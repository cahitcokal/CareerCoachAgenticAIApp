import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from career_shared.config import ServiceSettings


def test_sqlite_url_is_preserved():
    settings = ServiceSettings(database_url="sqlite:///./runtime/test.db")
    assert settings.resolved_database_url() == "sqlite:///./runtime/test.db"


def test_default_database_is_local_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = ServiceSettings()
    assert settings.resolved_database_url() == "sqlite:///runtime/career-service.db"


def test_postgres_urls_use_psycopg_driver():
    assert ServiceSettings(database_url="postgres://u:p@host/db").resolved_database_url() == (
        "postgresql+psycopg://u:p@host/db"
    )
    assert ServiceSettings(database_url="postgresql://u:p@host/db").resolved_database_url() == (
        "postgresql+psycopg://u:p@host/db"
    )
