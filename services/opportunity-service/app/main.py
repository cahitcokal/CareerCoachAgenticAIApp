"""Opportunity Service: opportunities, application steps, agent runs, audit.

Owns the core career data. Other services read/write through /internal/*
endpoints; the frontend uses bearer-token user endpoints.
"""
import json
import os
from datetime import datetime

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, selectinload

from app.models import AgentRun, ApplicationStep, Opportunity, PromptAuditLog
from career_shared.auth import get_current_user_id, verify_internal_key
from career_shared.client import ServiceClient
from career_shared.config import get_settings
from career_shared.cors import add_cors
from career_shared.db import get_db, init_db

app = FastAPI(title="Opportunity Service")
add_cors(app)
_personal_admin = ServiceClient(get_settings().personal_admin_url)

VALID_STATUSES = {"new", "active", "archived", "applied", "rejected", "interview"}


@app.on_event("startup")
def startup():
    init_db()


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "opportunity-service"}


# ---------- schemas ----------

class OpportunityIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    company: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=1000)
    profile_id: int | None = None
    source: str | None = "scout"
    status: str = "new"
    match_score: int | None = Field(default=None, ge=0, le=100)
    match_summary: str | None = None
    details: str | None = None


class OpportunityPatch(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    url: str | None = None
    status: str | None = None
    match_score: int | None = Field(default=None, ge=0, le=100)
    match_summary: str | None = None
    details: str | None = None
    relocation_report: str | None = None


class StepIn(BaseModel):
    step_order: int = 1
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    document_draft: str | None = None


class StepPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    document_draft: str | None = None
    completed: bool | None = None


class AgentRunIn(BaseModel):
    agent_name: str
    opportunity_id: int | None = None
    meta: dict | None = None


class AgentRunFinish(BaseModel):
    status: str = Field(pattern="^(success|failed|cancelled)$")
    error: str | None = None


class AuditLogIn(BaseModel):
    user_id: int | None = None
    opportunity_id: int | None = None
    agent_name: str
    provider: str | None = None
    model_name: str | None = None
    prompt_input: str | None = None
    response_output: str | None = None
    status: str = "success"
    error_message: str | None = None


# ---------- helpers ----------

def _profile_status_map(profile_ids: list[int]) -> dict:
    """Ask personal-admin which profiles are active; inactive ones hide data."""
    if not profile_ids:
        return {}
    try:
        resp = _personal_admin.get("/internal/profiles/status",
                                   params={"profile_ids": ",".join(map(str, profile_ids))})
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}


def _is_visible(opportunity: Opportunity, status_map: dict) -> bool:
    """Hide opportunities whose profile was soft-deleted or deactivated."""
    if opportunity.profile_id is None:
        return True
    status = status_map.get(str(opportunity.profile_id))
    if status is None:
        return True  # unknown profile: do not hide (e.g. service down)
    return bool(status.get("is_active")) and not status.get("deleted_at")


def _opp_dict(o: Opportunity, include_steps: bool = False) -> dict:
    data = {
        "id": o.id, "user_id": o.user_id, "profile_id": o.profile_id,
        "title": o.title, "company": o.company, "location": o.location,
        "url": o.url, "source": o.source, "status": o.status,
        "match_score": o.match_score, "match_summary": o.match_summary,
        "details": o.details, "relocation_report": o.relocation_report,
        "archived_at": o.archived_at.isoformat() if o.archived_at else None,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "updated_at": o.updated_at.isoformat() if o.updated_at else None,
    }
    if include_steps:
        data["steps"] = [_step_dict(s) for s in o.steps]
    return data


def _step_dict(s: ApplicationStep) -> dict:
    return {
        "id": s.id, "opportunity_id": s.opportunity_id, "step_order": s.step_order,
        "title": s.title, "description": s.description,
        "document_draft": s.document_draft, "completed": s.completed,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _get_opp(db: Session, opp_id: int, user_id: int | None = None) -> Opportunity:
    query = db.query(Opportunity).options(selectinload(Opportunity.steps)).filter(Opportunity.id == opp_id)
    if user_id is not None:
        query = query.filter(Opportunity.user_id == user_id)
    opp = query.first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


# ---------- user-facing opportunity endpoints ----------

@app.get("/opportunities")
def list_opportunities(
    status: str | None = Query(default=None),
    profile_id: int | None = Query(default=None),
    country: str | None = Query(default=None),
    company: str | None = Query(default=None),
    min_score: int | None = Query(default=None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    query = db.query(Opportunity).options(selectinload(Opportunity.steps)).filter(
        Opportunity.user_id == user_id)
    if status:
        query = query.filter(Opportunity.status == status)
    if profile_id:
        query = query.filter(Opportunity.profile_id == profile_id)
    if company:
        query = query.filter(Opportunity.company.ilike(f"%{company}%"))
    if min_score is not None:
        query = query.filter(Opportunity.match_score >= min_score)
    opportunities = query.order_by(Opportunity.id.desc()).all()

    # Filter out opportunities of inactive/deleted profiles.
    status_map = _profile_status_map([o.profile_id for o in opportunities if o.profile_id])
    opportunities = [o for o in opportunities if _is_visible(o, status_map)]

    # Country filter is applied on profile metadata stored in details JSON when present.
    if country:
        filtered = []
        for o in opportunities:
            if not o.details:
                continue
            try:
                meta = json.loads(o.details)
            except ValueError:
                continue
            countries = meta.get("countries") or meta.get("target_countries") or []
            if any(country.lower() in str(c).lower() for c in countries):
                filtered.append(o)
        opportunities = filtered

    return [_opp_dict(o, include_steps=True) for o in opportunities]


@app.post("/opportunities", status_code=201)
def create_opportunity(payload: OpportunityIn,
                       user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if payload.status and payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")
    opp = Opportunity(user_id=user_id, **payload.model_dump())
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return _opp_dict(opp)


@app.get("/opportunities/{opp_id}")
def get_opportunity(opp_id: int,
                    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    opp = _get_opp(db, opp_id, user_id)
    status_map = _profile_status_map([opp.profile_id] if opp.profile_id else [])
    if not _is_visible(opp, status_map):
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return _opp_dict(opp, include_steps=True)


@app.patch("/opportunities/{opp_id}")
def update_opportunity(opp_id: int, payload: OpportunityPatch,
                       user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    opp = _get_opp(db, opp_id, user_id)
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {data['status']}")
    for key, value in data.items():
        setattr(opp, key, value)
    db.commit()
    db.refresh(opp)
    return _opp_dict(opp, include_steps=True)


@app.delete("/opportunities/{opp_id}", status_code=204)
def delete_opportunity(opp_id: int,
                       user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    opp = _get_opp(db, opp_id, user_id)
    db.delete(opp)
    db.commit()
    return None


# ---------- steps ----------

@app.post("/opportunities/{opp_id}/steps", status_code=201)
def add_step(opp_id: int, payload: StepIn,
             user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    opp = _get_opp(db, opp_id, user_id)
    step = ApplicationStep(opportunity_id=opp.id, **payload.model_dump())
    db.add(step)
    db.commit()
    db.refresh(step)
    return _step_dict(step)


@app.patch("/opportunities/{opp_id}/steps/{step_id}")
def update_step(opp_id: int, step_id: int, payload: StepPatch,
                user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _get_opp(db, opp_id, user_id)
    step = db.query(ApplicationStep).filter(
        ApplicationStep.id == step_id, ApplicationStep.opportunity_id == opp_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(step, key, value)
    db.commit()
    return _step_dict(step)


@app.delete("/opportunities/{opp_id}/steps/{step_id}", status_code=204)
def delete_step(opp_id: int, step_id: int,
                user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _get_opp(db, opp_id, user_id)
    step = db.query(ApplicationStep).filter(
        ApplicationStep.id == step_id, ApplicationStep.opportunity_id == opp_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    db.delete(step)
    db.commit()
    return None


# ---------- agent runs ----------

@app.get("/agent-runs")
def list_agent_runs(agent_name: str | None = None,
                    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    query = db.query(AgentRun).filter(AgentRun.user_id == user_id)
    if agent_name:
        query = query.filter(AgentRun.agent_name == agent_name)
    runs = query.order_by(AgentRun.id.desc()).limit(50).all()
    return [{
        "id": r.id, "agent_name": r.agent_name, "status": r.status,
        "opportunity_id": r.opportunity_id, "meta": json.loads(r.meta) if r.meta else None,
        "error": r.error,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
    } for r in runs]


# ---------- internal endpoints ----------

@app.post("/internal/agent-runs", status_code=201)
def start_agent_run(payload: AgentRunIn, db: Session = Depends(get_db),
                    _: None = Depends(verify_internal_key)):
    """Register a run. Returns 409 if an identical run is already ongoing."""
    ongoing = db.query(AgentRun).filter(
        AgentRun.agent_name == payload.agent_name,
        AgentRun.user_id == (payload.meta or {}).get("user_id"),
        AgentRun.status == "running").first()
    if ongoing:
        raise HTTPException(status_code=409, detail="An agent run is already in progress")
    run = AgentRun(
        user_id=(payload.meta or {}).get("user_id"),
        agent_name=payload.agent_name,
        opportunity_id=payload.opportunity_id,
        meta=json.dumps(payload.meta) if payload.meta else None,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return {"id": run.id, "status": run.status}


@app.post("/internal/agent-runs/{run_id}/finish")
def finish_agent_run(run_id: int, payload: AgentRunFinish,
                     db: Session = Depends(get_db), _: None = Depends(verify_internal_key)):
    run = db.get(AgentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run.status = payload.status
    run.error = payload.error
    run.finished_at = datetime.utcnow()
    db.commit()
    return {"id": run.id, "status": run.status}


@app.get("/internal/agent-runs/ongoing")
def ongoing_runs(agent_name: str, user_id: int,
                 db: Session = Depends(get_db), _: None = Depends(verify_internal_key)):
    runs = db.query(AgentRun).filter(
        AgentRun.agent_name == agent_name,
        AgentRun.user_id == user_id,
        AgentRun.status == "running").all()
    return [{"id": r.id, "started_at": r.started_at.isoformat() if r.started_at else None}
            for r in runs]


@app.get("/internal/opportunities")
def internal_list_opportunities(user_id: int, status: str | None = None,
                                profile_id: int | None = None,
                                db: Session = Depends(get_db),
                                _: None = Depends(verify_internal_key)):
    query = db.query(Opportunity).filter(Opportunity.user_id == user_id)
    if status:
        query = query.filter(Opportunity.status == status)
    if profile_id:
        query = query.filter(Opportunity.profile_id == profile_id)
    return [_opp_dict(o, include_steps=True)
            for o in query.order_by(Opportunity.id.desc()).all()]


@app.get("/internal/opportunities/{opp_id}")
def internal_get_opportunity(opp_id: int, db: Session = Depends(get_db),
                             _: None = Depends(verify_internal_key)):
    return _opp_dict(_get_opp(db, opp_id), include_steps=True)


@app.post("/internal/opportunities", status_code=201)
def internal_create_opportunity(payload: OpportunityIn, user_id: int,
                                db: Session = Depends(get_db),
                                _: None = Depends(verify_internal_key)):
    """Agents persist discovered opportunities here."""
    opp = Opportunity(user_id=user_id, **payload.model_dump())
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return _opp_dict(opp)


@app.patch("/internal/opportunities/{opp_id}")
def internal_update_opportunity(opp_id: int, payload: OpportunityPatch,
                                db: Session = Depends(get_db),
                                _: None = Depends(verify_internal_key)):
    opp = _get_opp(db, opp_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(opp, key, value)
    db.commit()
    db.refresh(opp)
    return _opp_dict(opp)


@app.delete("/internal/opportunities/{opp_id}/steps")
def internal_clear_steps(opp_id: int, db: Session = Depends(get_db),
                         _: None = Depends(verify_internal_key)):
    """Replace-all helper: agents clear steps before regenerating."""
    opp = _get_opp(db, opp_id)
    for step in list(opp.steps):
        db.delete(step)
    db.commit()
    return {"cleared": True}


@app.post("/internal/opportunities/{opp_id}/steps", status_code=201)
def internal_add_steps(opp_id: int, steps: list[StepIn], db: Session = Depends(get_db),
                       _: None = Depends(verify_internal_key)):
    opp = _get_opp(db, opp_id)
    created = []
    for step_payload in steps:
        step = ApplicationStep(opportunity_id=opp.id, **step_payload.model_dump())
        db.add(step)
        created.append(step)
    db.commit()
    for step in created:
        db.refresh(step)
    return [_step_dict(s) for s in created]


@app.post("/internal/audit-logs", status_code=201)
def create_audit_log(payload: AuditLogIn, db: Session = Depends(get_db),
                     _: None = Depends(verify_internal_key)):
    log = PromptAuditLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"id": log.id}


@app.get("/internal/audit-logs")
def list_audit_logs(user_id: int | None = None, opportunity_id: int | None = None,
                    agent_name: str | None = None, limit: int = 100,
                    db: Session = Depends(get_db), _: None = Depends(verify_internal_key)):
    query = db.query(PromptAuditLog)
    if user_id is not None:
        query = query.filter(PromptAuditLog.user_id == user_id)
    if opportunity_id is not None:
        query = query.filter(PromptAuditLog.opportunity_id == opportunity_id)
    if agent_name:
        query = query.filter(PromptAuditLog.agent_name == agent_name)
    rows = query.order_by(PromptAuditLog.id.desc()).limit(min(limit, 500)).all()
    return [{
        "id": r.id, "user_id": r.user_id, "opportunity_id": r.opportunity_id,
        "agent_name": r.agent_name, "provider": r.provider, "model_name": r.model_name,
        "prompt_input": r.prompt_input, "response_output": r.response_output,
        "status": r.status, "error_message": r.error_message,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in rows]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8004))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
