"""Service configuration via environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "career-service"
    database_url: str = "postgresql+psycopg://career:career@localhost:5432/career"
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


@lru_cache
def get_settings() -> ServiceSettings:
    return ServiceSettings()
