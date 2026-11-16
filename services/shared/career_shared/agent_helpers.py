"""Shared agent-run helpers: audit logging and profile formatting."""
import json
import logging

from career_shared.client import ServiceClient
from career_shared.config import get_settings

logger = logging.getLogger(__name__)

_opportunities = ServiceClient(get_settings().opportunity_service_url, timeout=15.0)


def format_profile_for_prompt(profile: dict | None) -> str:
    if not profile:
        return "Standart Profesyonel Profil"
    fields = ("name", "title", "demographics", "education", "experience",
              "certifications", "preferences")
    return json.dumps({f: profile.get(f) for f in fields},
                      ensure_ascii=False, separators=(",", ":"))


def write_audit(agent_name: str, provider: str | None, model_name: str | None,
                prompt_input: str, *, user_id=None, opportunity_id=None,
                response_output=None, status="success", error_message=None) -> None:
    """Best-effort audit write; never breaks the agent run."""
    try:
        _opportunities.post("/internal/audit-logs", json={
            "user_id": user_id, "opportunity_id": opportunity_id,
            "agent_name": agent_name, "provider": provider, "model_name": model_name,
            "prompt_input": prompt_input, "response_output": response_output,
            "status": status, "error_message": error_message,
        })
    except Exception as exc:
        logger.error("Audit write failed for %s: %s", agent_name, type(exc).__name__)
