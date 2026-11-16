"""System Admin Service: languages, providers, agent LLM configuration.

Stores all configuration in its own database. API keys are encrypted at rest
with Fernet (SETTINGS_ENCRYPTION_KEY) — same approach as the original monolith.
"""
import os
import secrets
from datetime import datetime

import uvicorn
from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Session

from career_shared.auth import get_current_user_id, verify_internal_key
from career_shared.cors import add_cors
from career_shared.db import Base, get_db, get_session_local, init_db
from career_shared.config import get_settings

app = FastAPI(title="System Admin Service")
add_cors(app)


# ---------- models ----------

class LanguageSetting(Base):
    __tablename__ = "language_settings"

    code = Column(String(10), primary_key=True)
    name = Column(String(50), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)


class ProviderCredential(Base):
    __tablename__ = "provider_credentials"

    provider = Column(String(30), primary_key=True)
    display_name = Column(String(100), nullable=False)
    base_url = Column(String(500), nullable=True)
    encrypted_api_key = Column(Text, nullable=True)
    priority = Column(Integer, default=100, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProviderModel(Base):
    __tablename__ = "provider_models"
    __table_args__ = (UniqueConstraint("provider", "model", name="uq_provider_model"),)

    id = Column(Integer, primary_key=True)
    provider = Column(String(30), nullable=False, index=True)
    model = Column(String(150), nullable=False)
    priority = Column(Integer, default=100, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)


class AgentSetting(Base):
    __tablename__ = "agent_settings"

    agent_name = Column(String(50), primary_key=True)
    display_name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    provider_order = Column(Text, nullable=False, default="")  # JSON list of provider names
    max_attempts = Column(Integer, default=3, nullable=False)
    max_retry_delay = Column(Integer, default=60, nullable=False)
    max_turns = Column(Integer, default=4, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SettingsAudit(Base):
    __tablename__ = "settings_audit"

    id = Column(Integer, primary_key=True)
    actor_user_id = Column(Integer, nullable=True)
    entity = Column(String(50), nullable=False)
    entity_key = Column(String(150), nullable=False)
    action = Column(String(20), nullable=False)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


AGENTS = ["scout", "relocation", "application_coach"]
PROVIDERS = ["gemini", "openai", "anthropic", "groq", "ollama"]
DEFAULT_LANGUAGES = [("tr", "Türkçe"), ("en", "English")]


def _fernet() -> Fernet | None:
    key = os.getenv("SETTINGS_ENCRYPTION_KEY")
    if not key:
        return None
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError):
        return None


def encrypt_secret(value: str) -> str | None:
    f = _fernet()
    if not f:
        return None
    return f.encrypt(value.encode()).decode()


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    f = _fernet()
    if not f:
        return None
    try:
        return f.decrypt(value.encode()).decode()
    except InvalidToken:
        return None


def audit(db: Session, actor: int | None, entity: str, key: str, action: str, detail: str = ""):
    db.add(SettingsAudit(actor_user_id=actor, entity=entity, entity_key=key,
                         action=action, detail=detail[:2000]))
    db.commit()


def _require_admin(user_id: int, db: Session):
    # System admin role lives in user-management; check via internal call.
    from career_shared.client import ServiceClient
    settings = get_settings()
    resp = ServiceClient(settings.user_management_url).get(
        f"/internal/users/{user_id}/is-system-admin")
    if resp.status_code != 200 or not resp.json().get("is_system_admin"):
        raise HTTPException(status_code=403, detail="System administrator access required")


# ---------- schemas ----------

class LanguageIn(BaseModel):
    code: str = Field(min_length=2, max_length=10)
    name: str = Field(min_length=1, max_length=50)
    enabled: bool = True
    is_default: bool = False
    sort_order: int = 0


class ProviderIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    base_url: str | None = Field(default=None, max_length=500)
    api_key: str | None = None  # write-only; never returned
    priority: int = 100
    enabled: bool = True


class ProviderPatch(BaseModel):
    display_name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    priority: int | None = None
    enabled: bool | None = None


class ModelIn(BaseModel):
    model: str = Field(min_length=1, max_length=150)
    priority: int = 100
    enabled: bool = True


class ModelPatch(BaseModel):
    priority: int | None = None
    enabled: bool | None = None


class AgentIn(BaseModel):
    enabled: bool = True
    provider_order: list[str] = Field(default_factory=list)
    max_attempts: int = Field(default=3, ge=1, le=10)
    max_retry_delay: int = Field(default=60, ge=0, le=600)
    max_turns: int = Field(default=4, ge=1, le=50)


# ---------- helpers ----------

def _language_dict(l: LanguageSetting) -> dict:
    return {"code": l.code, "name": l.name, "enabled": l.enabled,
            "is_default": l.is_default, "sort_order": l.sort_order}


def _provider_dict(p: ProviderCredential, db: Session) -> dict:
    return {
        "provider": p.provider, "display_name": p.display_name,
        "base_url": p.base_url, "priority": p.priority, "enabled": p.enabled,
        "has_api_key": bool(p.encrypted_api_key),
        "models": [_model_dict(m) for m in db.query(ProviderModel)
                   .filter(ProviderModel.provider == p.provider)
                   .order_by(ProviderModel.priority, ProviderModel.id).all()],
    }


def _model_dict(m: ProviderModel) -> dict:
    return {"id": m.id, "model": m.model, "priority": m.priority, "enabled": m.enabled}


def _agent_dict(a: AgentSetting) -> dict:
    import json
    return {
        "agent_name": a.agent_name, "display_name": a.display_name,
        "enabled": a.enabled, "provider_order": json.loads(a.provider_order or "[]"),
        "max_attempts": a.max_attempts, "max_retry_delay": a.max_retry_delay,
        "max_turns": a.max_turns, "description": a.description,
    }


def _seed(db: Session):
    if db.query(LanguageSetting).count() == 0:
        for i, (code, name) in enumerate(DEFAULT_LANGUAGES):
            db.add(LanguageSetting(code=code, name=name, enabled=True,
                                   is_default=(code == "tr"), sort_order=i))
    for provider in PROVIDERS:
        if not db.get(ProviderCredential, provider):
            db.add(ProviderCredential(provider=provider,
                                      display_name=provider.capitalize(),
                                      priority=PROVIDERS.index(provider)))
    for agent in AGENTS:
        if not db.get(AgentSetting, agent):
            db.add(AgentSetting(agent_name=agent,
                                display_name=agent.replace("_", " ").title()))
    db.commit()


@app.on_event("startup")
def startup():
    init_db()
    db = get_session_local()()
    try:
        _seed(db)
    finally:
        db.close()


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "system-admin"}


# ---------- languages ----------

@app.get("/languages/public")
def public_languages(db: Session = Depends(get_db)):
    """Enabled languages + default — safe for anonymous frontend bootstrap."""
    rows = db.query(LanguageSetting).order_by(LanguageSetting.sort_order).all()
    enabled = [l for l in rows if l.enabled]
    default = next((l for l in enabled if l.is_default), enabled[0] if enabled else None)
    return {"default": _language_dict(default) if default else None,
            "languages": [_language_dict(l) for l in enabled]}


@app.get("/languages")
def list_languages(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    return [_language_dict(l) for l in db.query(LanguageSetting)
            .order_by(LanguageSetting.sort_order).all()]


@app.put("/languages/{code}")
def update_language(code: str, payload: LanguageIn,
                    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    lang = db.get(LanguageSetting, code)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    enabled_count = db.query(LanguageSetting).filter(LanguageSetting.enabled.is_(True)).count()
    if lang.enabled and not payload.enabled and enabled_count <= 1:
        raise HTTPException(status_code=400, detail="At least one language must stay enabled")
    if payload.is_default:
        for other in db.query(LanguageSetting).all():
            other.is_default = other.code == code
        if not payload.enabled:
            raise HTTPException(status_code=400, detail="Default language must be enabled")
    for key, value in payload.model_dump().items():
        setattr(lang, key, value)
    db.commit()
    audit(db, user_id, "language", code, "update")
    return _language_dict(lang)


@app.post("/languages/{code}/set-default")
def set_default_language(code: str,
                         user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    lang = db.get(LanguageSetting, code)
    if not lang or not lang.enabled:
        raise HTTPException(status_code=400, detail="Cannot default a disabled language")
    for other in db.query(LanguageSetting).all():
        other.is_default = other.code == code
    db.commit()
    audit(db, user_id, "language", code, "set_default")
    return _language_dict(lang)


# ---------- providers ----------

@app.get("/providers")
def list_providers(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    rows = db.query(ProviderCredential).order_by(ProviderCredential.priority).all()
    return [_provider_dict(p, db) for p in rows]


@app.put("/providers/{provider}")
def upsert_provider(provider: str, payload: ProviderIn,
                    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    cred = db.get(ProviderCredential, provider)
    if not cred:
        cred = ProviderCredential(provider=provider)
        db.add(cred)
    cred.display_name = payload.display_name
    cred.base_url = payload.base_url
    cred.priority = payload.priority
    cred.enabled = payload.enabled
    if payload.api_key is not None:
        cred.encrypted_api_key = encrypt_secret(payload.api_key)
    db.commit()
    audit(db, user_id, "provider", provider, "upsert")
    return _provider_dict(cred, db)


@app.patch("/providers/{provider}")
def patch_provider(provider: str, payload: ProviderPatch,
                   user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    cred = db.get(ProviderCredential, provider)
    if not cred:
        raise HTTPException(status_code=404, detail="Provider not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "api_key":
            if value is not None:
                cred.encrypted_api_key = encrypt_secret(value)
        else:
            setattr(cred, key, value)
    db.commit()
    audit(db, user_id, "provider", provider, "patch")
    return _provider_dict(cred, db)


# ---------- provider models ----------

@app.post("/providers/{provider}/models", status_code=201)
def add_model(provider: str, payload: ModelIn,
              user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    if not db.get(ProviderCredential, provider):
        raise HTTPException(status_code=404, detail="Provider not found")
    existing = db.query(ProviderModel).filter_by(provider=provider, model=payload.model).first()
    if existing:
        existing.priority = payload.priority
        existing.enabled = payload.enabled
    else:
        existing = ProviderModel(provider=provider, model=payload.model,
                                 priority=payload.priority, enabled=payload.enabled)
        db.add(existing)
    db.commit()
    audit(db, user_id, "provider_model", f"{provider}:{payload.model}", "upsert")
    return _model_dict(existing)


@app.patch("/providers/{provider}/models/{model_id}")
def patch_model(provider: str, model_id: int, payload: ModelPatch,
                user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    model = db.query(ProviderModel).filter_by(id=model_id, provider=provider).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(model, key, value)
    db.commit()
    audit(db, user_id, "provider_model", f"{provider}:{model.model}", "patch")
    return _model_dict(model)


@app.delete("/providers/{provider}/models/{model_id}", status_code=204)
def delete_model(provider: str, model_id: int,
                 user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    model = db.query(ProviderModel).filter_by(id=model_id, provider=provider).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    db.delete(model)
    db.commit()
    return None


# ---------- agent settings ----------

@app.get("/agents")
def list_agents(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    return [_agent_dict(a) for a in db.query(AgentSetting).order_by(AgentSetting.agent_name).all()]


@app.put("/agents/{agent_name}")
def update_agent(agent_name: str, payload: AgentIn,
                 user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    agent = db.get(AgentSetting, agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    import json
    agent.enabled = payload.enabled
    agent.provider_order = json.dumps(payload.provider_order)
    agent.max_attempts = payload.max_attempts
    agent.max_retry_delay = payload.max_retry_delay
    agent.max_turns = payload.max_turns
    db.commit()
    audit(db, user_id, "agent", agent_name, "update")
    return _agent_dict(agent)


# ---------- internal endpoints (LLM router + agents) ----------

@app.get("/internal/agents/{agent_name}/config")
def internal_agent_config(agent_name: str, db: Session = Depends(get_db),
                          _: None = Depends(verify_internal_key)):
    """Runtime config consumed by career_shared.llm.router."""
    agent = db.get(AgentSetting, agent_name)
    import json
    if not agent:
        return {"enabled": True, "providers": [], "max_attempts": 3,
                "max_retry_delay": 60, "max_turns": 4}
    order = json.loads(agent.provider_order or "[]")
    providers = []
    for provider_name in order:
        cred = db.get(ProviderCredential, provider_name)
        if not cred or not cred.enabled:
            continue
        models = [m.model for m in db.query(ProviderModel)
                  .filter(ProviderModel.provider == provider_name,
                          ProviderModel.enabled.is_(True))
                  .order_by(ProviderModel.priority, ProviderModel.id).all()]
        providers.append({
            "provider": provider_name,
            "models": models,
            "api_key": decrypt_secret(cred.encrypted_api_key),
            "base_url": cred.base_url,
        })
    return {
        "agent_name": agent_name,
        "enabled": agent.enabled,
        "providers": providers,
        "max_attempts": agent.max_attempts,
        "max_retry_delay": agent.max_retry_delay,
        "max_turns": agent.max_turns,
    }


@app.get("/internal/languages")
def internal_languages(db: Session = Depends(get_db), _: None = Depends(verify_internal_key)):
    rows = db.query(LanguageSetting).order_by(LanguageSetting.sort_order).all()
    enabled = [l for l in rows if l.enabled]
    default = next((l for l in enabled if l.is_default), enabled[0] if enabled else None)
    return {"default": _language_dict(default) if default else None,
            "languages": [_language_dict(l) for l in enabled]}


@app.get("/internal/audit")
def internal_audit(limit: int = 50, db: Session = Depends(get_db),
                   _: None = Depends(verify_internal_key)):
    rows = db.query(SettingsAudit).order_by(SettingsAudit.id.desc()).limit(limit).all()
    return [{"id": r.id, "actor_user_id": r.actor_user_id, "entity": r.entity,
             "entity_key": r.entity_key, "action": r.action, "detail": r.detail,
             "created_at": r.created_at.isoformat() if r.created_at else None}
            for r in rows]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8003))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
