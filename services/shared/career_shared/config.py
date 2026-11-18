"""Service configuration via environment variables.

Database selection is URL-based. SQLite, PostgreSQL, Supabase, and Neon all
go through the same SQLAlchemy boundary; Supabase and Neon use PostgreSQL URLs.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "career-service"
    # A URL is the only database-specific value services need to know.
    database_url: str | None = None
    database_provider: str = "auto"
    sqlite_path: str = "runtime/career-service.db"
    jwt_secret: str = "dev-only-change-me-please-32chars-min"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    user_management_url: str = "http://localhost:8001"
    personal_admin_url: str = "http://localhost:8002"
    system_admin_url: str = "http://localhost:8003"
    opportunity_service_url: str = "http://localhost:8004"
    scout_agent_url: str = "http://localhost:8005"
    relocation_agent_url: str = "http://localhost:8006"
    application_coach_agent_url: str = "http://localhost:8007"
    internal_api_key: str = "dev-internal-key"
    frontend_url: str = "http://localhost:3000"

    def resolved_database_url(self) -> str:
        """Return a SQLAlchemy URL compatible with the shared DB adapter."""
        url = (self.database_url or "").strip()
        if not url:
            provider = self.database_provider.strip().lower()
            if provider not in {"auto", "sqlite"}:
                raise ValueError(
                    f"DATABASE_URL is required when DATABASE_PROVIDER={self.database_provider!r}"
                )
            path = Path(self.sqlite_path).as_posix()
            return f"sqlite:///{path}"
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url.removeprefix("postgres://")
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url.removeprefix("postgresql://")
        return url


@lru_cache
def get_settings() -> ServiceSettings:
    return ServiceSettings()
