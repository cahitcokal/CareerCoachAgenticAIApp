"""Application Coach Agent: async application steps + document drafts."""
import json
import logging
import os

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from pydantic import BaseModel

from career_shared.agent_helpers import format_profile_for_prompt, write_audit
from career_shared.auth import get_current_user_id
from career_shared.client import ServiceClient
from career_shared.config import get_settings
from career_shared.cors import add_cors
from career_shared.llm import invoke_json

logger = logging.getLogger(__name__)
app = FastAPI(title="Application Coach Agent")
add_cors(app)

_opportunities = ServiceClient(get_settings().opportunity_service_url, timeout=60.0)
_personal_admin = ServiceClient(get_settings().personal_admin_url, timeout=15.0)

AGENT_NAME = "application_coach"


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "application-coach-agent"}


class CoachRequest(BaseModel):
    opportunity_id: int
    profile_id: int | None = None


def _start_run(user_id: int, opportunity_id: int) -> int:
    resp = _opportunities.post("/internal/agent-runs", json={
        "agent_name": AGENT_NAME, "opportunity_id": opportunity_id,
        "meta": {"user_id": user_id}})
    if resp.status_code == 409:
        raise HTTPException(status_code=409, detail="A coach run is already in progress")
    resp.raise_for_status()
    return resp.json()["id"]


def _finish_run(run_id: int, status: str, error: str | None = None):
    try:
        _opportunities.post(f"/internal/agent-runs/{run_id}/finish",
                            json={"status": status, "error": error})
    except Exception as exc:
        logger.error("Failed to finish agent run %s: %s", run_id, type(exc).__name__)


def _fetch_profile(user_id: int, profile_id: int | None) -> dict | None:
    try:
        if profile_id:
            resp = _personal_admin.get(f"/internal/profiles/{profile_id}")
            return resp.json() if resp.status_code == 200 else None
        resp = _personal_admin.get("/internal/profiles", params={"user_id": user_id})
        data = resp.json()
        return data[0] if data else None
    except Exception:
        return None


def _run_coach(run_id: int, user_id: int, payload: CoachRequest):
    try:
        opp_resp = _opportunities.get(f"/internal/opportunities/{payload.opportunity_id}")
        if opp_resp.status_code != 200:
            raise RuntimeError(f"Opportunity {payload.opportunity_id} not found")
        opportunity = opp_resp.json()
        profile = _fetch_profile(user_id, payload.profile_id or opportunity.get("profile_id"))

        prompt = f"""You are an application coach agent. Build an actionable
application plan with document drafts for this opportunity.

Opportunity (JSON): {json.dumps(opportunity, ensure_ascii=False)}
Candidate profile (JSON): {format_profile_for_prompt(profile)}

Return ONLY a JSON array of step objects with keys:
step_order (int), title, description, document_draft (markdown text for cover
letter / CV tailoring / answers as appropriate).
"""

        def on_attempt(**kwargs):
            write_audit(AGENT_NAME, kwargs.get("provider"), kwargs.get("model"),
                        prompt, user_id=user_id, opportunity_id=payload.opportunity_id,
                        status="attempt")

        steps = invoke_json(AGENT_NAME, prompt, as_list=True, user_id=user_id,
                            opportunity_id=payload.opportunity_id, on_attempt=on_attempt)

        # Replace previous steps, then insert the new plan.
        _opportunities.delete(f"/internal/opportunities/{payload.opportunity_id}/steps")
        normalized = []
        for index, step in enumerate(steps if isinstance(steps, list) else [], start=1):
            if not isinstance(step, dict) or not step.get("title"):
                continue
            normalized.append({
                "step_order": step.get("step_order") or index,
                "title": str(step["title"])[:300],
                "description": step.get("description"),
                "document_draft": step.get("document_draft"),
            })
        if normalized:
            _opportunities.post(
                f"/internal/opportunities/{payload.opportunity_id}/steps",
                json=normalized)
        # Mark the opportunity as having an active application in progress.
        _opportunities.patch(f"/internal/opportunities/{payload.opportunity_id}",
                             json={"status": "active"})
        _finish_run(run_id, "success")
        return normalized
    except Exception as exc:
        logger.exception("Coach run %s failed", run_id)
        _finish_run(run_id, "failed", str(exc)[:500])
        # Audit failures must not flip a successful run to failed — _finish_run
        # already recorded the outcome; re-raise only for background logging.
        raise


@app.post("/application-steps", status_code=202)
def application_steps(payload: CoachRequest, background: BackgroundTasks,
                      user_id: int = Depends(get_current_user_id)):
    resp = _opportunities.get("/internal/opportunities", params={"user_id": user_id})
    if resp.status_code == 200:
        owned = {o["id"] for o in resp.json()}
        if payload.opportunity_id not in owned:
            raise HTTPException(status_code=404, detail="Opportunity not found")
    run_id = _start_run(user_id, payload.opportunity_id)
    background.add_task(_run_coach, run_id, user_id, payload)
    return {"run_id": run_id, "status": "running"}


@app.get("/runs")
def list_runs(user_id: int = Depends(get_current_user_id)):
    resp = _opportunities.get("/internal/agent-runs/ongoing",
                              params={"agent_name": AGENT_NAME, "user_id": user_id})
    return resp.json() if resp.status_code == 200 else []


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8007))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
