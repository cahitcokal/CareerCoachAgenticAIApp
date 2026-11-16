"""Scout Agent: asynchronous job search, matching, scoring, persistence.

Flow: POST /search -> registers an agent run (409 if one is ongoing), runs the
LLM-driven search in a background task, persists opportunities via the
opportunity-service, and finishes the run.
"""
import json
import logging
import os
from typing import Any

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from career_shared.agent_helpers import format_profile_for_prompt, write_audit
from career_shared.auth import get_current_user_id
from career_shared.client import ServiceClient
from career_shared.config import get_settings
from career_shared.cors import add_cors
from career_shared.llm import invoke_json

logger = logging.getLogger(__name__)
app = FastAPI(title="Scout Agent")
add_cors(app)

_opportunities = ServiceClient(get_settings().opportunity_service_url, timeout=60.0)
_personal_admin = ServiceClient(get_settings().personal_admin_url, timeout=15.0)

AGENT_NAME = "scout"


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "scout-agent"}


class SearchRequest(BaseModel):
    profile_id: int | None = None
    query: str | None = Field(default=None, max_length=500)
    locations: list[str] = Field(default_factory=list)
    max_results: int = Field(default=10, ge=1, le=50)


class UrlAnalysisRequest(BaseModel):
    url: str = Field(min_length=8, max_length=1000)
    profile_id: int | None = None


def _start_run(user_id: int, meta: dict) -> int:
    resp = _opportunities.post("/internal/agent-runs", json={
        "agent_name": AGENT_NAME, "meta": {"user_id": user_id, **meta}})
    if resp.status_code == 409:
        raise HTTPException(status_code=409, detail="A scout search is already running")
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
        else:
            resp = _personal_admin.get("/internal/profiles", params={"user_id": user_id})
            data = resp.json()
            resp = type("R", (), {"status_code": 200, "json": lambda s: (data[0] if data else None)})()
        if resp.status_code == 200 and resp.json():
            return resp.json()
    except Exception as exc:
        logger.warning("Profile fetch failed: %s", type(exc).__name__)
    return None


def _build_search_prompt(profile: dict | None, payload: SearchRequest, user_id: int) -> str:
    profile_text = format_profile_for_prompt(profile)
    try:
        targets_resp = _personal_admin.get("/internal/targets", params={"user_id": user_id})
        targets_text = targets_resp.json() if targets_resp.status_code == 200 else {}
    except Exception:
        targets_text = {}
    return f"""You are a career scout agent. Find relevant job opportunities.

Candidate profile (JSON): {profile_text}
Target countries: {json.dumps([c.get('name') for c in targets_text.get('countries', [])], ensure_ascii=False)}
Target roles: {json.dumps([r.get('name') for r in targets_text.get('roles', [])], ensure_ascii=False)}
Target career sites: {json.dumps([s.get('name') for s in targets_text.get('career_sites', [])], ensure_ascii=False)}
User query: {payload.query or 'Find the best matching jobs'}
Preferred locations: {', '.join(payload.locations) or 'any'}
Maximum results: {payload.max_results}

Return ONLY a JSON array of objects with keys:
title, company, location, url, match_score (0-100), match_summary, details (JSON string with countries/target_countries).
"""


def _run_search(run_id: int, user_id: int, payload: SearchRequest):
    try:
        profile = _fetch_profile(user_id, payload.profile_id)
        prompt = _build_search_prompt(profile, payload, user_id)

        def on_attempt(**kwargs):
            write_audit(AGENT_NAME, kwargs.get("provider"), kwargs.get("model"),
                        prompt, user_id=user_id, status="attempt")

        results = invoke_json(AGENT_NAME, prompt, as_list=True, web_search=True,
                              user_id=user_id, on_attempt=on_attempt)
        created = []
        for item in results[: payload.max_results]:
            if not isinstance(item, dict) or not item.get("title"):
                continue
            resp = _opportunities.post("/internal/opportunities", params={"user_id": user_id}, json={
                "title": item.get("title"),
                "company": item.get("company"),
                "location": item.get("location"),
                "url": item.get("url"),
                "profile_id": payload.profile_id,
                "source": "scout",
                "status": "new",
                "match_score": item.get("match_score"),
                "match_summary": item.get("match_summary"),
                "details": item.get("details") if isinstance(item.get("details"), str)
                           else json.dumps(item.get("details"), ensure_ascii=False),
            })
            if resp.status_code in (200, 201):
                created.append(resp.json())
        _finish_run(run_id, "success")
        return created
    except Exception as exc:
        logger.exception("Scout run %s failed", run_id)
        _finish_run(run_id, "failed", str(exc)[:500])
        raise


def _run_url_analysis(run_id: int, user_id: int, payload: UrlAnalysisRequest):
    try:
        profile = _fetch_profile(user_id, payload.profile_id)
        prompt = f"""Analyze this job posting URL and extract structured opportunity data.
URL: {payload.url}
Candidate profile (JSON): {format_profile_for_prompt(profile)}
Return ONLY a JSON object with keys: title, company, location, url, match_score (0-100), match_summary, details.
"""
        data = invoke_json(AGENT_NAME, prompt, web_search=True, user_id=user_id)
        if not isinstance(data, dict):
            data = {}
        data.setdefault("url", payload.url)
        resp = _opportunities.post("/internal/opportunities", params={"user_id": user_id}, json={
            "title": data.get("title") or payload.url,
            "company": data.get("company"),
            "location": data.get("location"),
            "url": data.get("url") or payload.url,
            "profile_id": payload.profile_id,
            "source": "scout-url",
            "status": "new",
            "match_score": data.get("match_score"),
            "match_summary": data.get("match_summary"),
            "details": data.get("details") if isinstance(data.get("details"), str)
                       else json.dumps(data.get("details") or {}, ensure_ascii=False),
        })
        _finish_run(run_id, "success")
        return resp.json() if resp.status_code in (200, 201) else None
    except Exception as exc:
        logger.exception("URL analysis run %s failed", run_id)
        _finish_run(run_id, "failed", str(exc)[:500])
        raise


@app.post("/search", status_code=202)
def search(payload: SearchRequest, background: BackgroundTasks,
           user_id: int = Depends(get_current_user_id)):
    run_id = _start_run(user_id, {"kind": "search", "query": payload.query})
    background.add_task(_run_search, run_id, user_id, payload)
    return {"run_id": run_id, "status": "running"}


@app.post("/analyze-url", status_code=202)
def analyze_url(payload: UrlAnalysisRequest, background: BackgroundTasks,
                user_id: int = Depends(get_current_user_id)):
    run_id = _start_run(user_id, {"kind": "url_analysis", "url": payload.url})
    background.add_task(_run_url_analysis, run_id, user_id, payload)
    return {"run_id": run_id, "status": "running"}


@app.get("/runs")
def list_runs(user_id: int = Depends(get_current_user_id)):
    resp = _opportunities.get("/internal/agent-runs/ongoing",
                              params={"agent_name": AGENT_NAME, "user_id": user_id})
    return resp.json() if resp.status_code == 200 else []


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8005))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
