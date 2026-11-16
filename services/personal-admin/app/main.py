"""Personal Admin Service: profiles (soft delete), target lists, language pref."""
import os
from datetime import datetime

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models import TargetCareerSite, TargetCountry, TargetRole, UserPreference, UserProfile
from career_shared.auth import get_current_user_id, verify_internal_key
from career_shared.cors import add_cors
from career_shared.db import get_db, init_db

app = FastAPI(title="Personal Admin Service")
add_cors(app)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "personal-admin"}


# ---------- schemas ----------

class ProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    title: str | None = Field(default=None, max_length=150)
    demographics: str | None = None
    education: str | None = None
    experience: str | None = None
    certifications: str | None = None
    preferences: str | None = None
    is_active: bool = True


class ProfilePatch(BaseModel):
    name: str | None = None
    title: str | None = None
    demographics: str | None = None
    education: str | None = None
    experience: str | None = None
    certifications: str | None = None
    preferences: str | None = None
    is_active: bool | None = None


class NamedItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    notes: str | None = None
    url: str | None = Field(default=None, max_length=500)


class NamedItemPatch(BaseModel):
    name: str | None = None
    notes: str | None = None
    url: str | None = Field(default=None, max_length=500)


class PreferencesIn(BaseModel):
    language: str | None = Field(default=None, max_length=10)


DEFAULT_COUNTRIES = ["Germany", "Netherlands", "United Kingdom", "United States", "Canada"]
DEFAULT_SITES = ["LinkedIn", "Indeed", "Glassdoor", "Xing"]
DEFAULT_ROLES = ["Software Engineer", "Data Engineer", "Product Manager", "DevOps Engineer"]


def _profile_dict(p: UserProfile) -> dict:
    return {
        "id": p.id, "user_id": p.user_id, "name": p.name, "title": p.title,
        "demographics": p.demographics, "education": p.education,
        "experience": p.experience, "certifications": p.certifications,
        "preferences": p.preferences, "is_active": p.is_active,
        "deleted_at": p.deleted_at.isoformat() if p.deleted_at else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def _named_dict(item, extra: dict | None = None) -> dict:
    data = {"id": item.id, "user_id": item.user_id, "name": item.name,
            "notes": getattr(item, "notes", None), "created_at": item.created_at.isoformat() if item.created_at else None}
    if hasattr(item, "url"):
        data["url"] = item.url
    if extra:
        data.update(extra)
    return data


# ---------- profiles ----------

@app.get("/profiles")
def list_profiles(include_deleted: bool = False,
                  user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    query = db.query(UserProfile).filter(UserProfile.user_id == user_id)
    if not include_deleted:
        query = query.filter(UserProfile.deleted_at.is_(None))
    profiles = query.order_by(UserProfile.id).all()
    return [_profile_dict(p) for p in profiles]


@app.post("/profiles", status_code=201)
def create_profile(payload: ProfileIn,
                   user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    profile = UserProfile(user_id=user_id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _profile_dict(profile)


def _get_profile(db: Session, user_id: int, profile_id: int) -> UserProfile:
    profile = db.query(UserProfile).filter(
        UserProfile.id == profile_id, UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.get("/profiles/{profile_id}")
def get_profile(profile_id: int,
                user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return _profile_dict(_get_profile(db, user_id, profile_id))


@app.patch("/profiles/{profile_id}")
def update_profile(profile_id: int, payload: ProfilePatch,
                   user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    profile = _get_profile(db, user_id, profile_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return _profile_dict(profile)


@app.delete("/profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: int,
                   user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Soft delete: marks the profile inactive and stamps deleted_at."""
    profile = _get_profile(db, user_id, profile_id)
    profile.is_active = False
    profile.deleted_at = datetime.utcnow()
    db.commit()
    return None


@app.post("/profiles/{profile_id}/restore")
def restore_profile(profile_id: int,
                    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    profile = _get_profile(db, user_id, profile_id)
    profile.is_active = True
    profile.deleted_at = None
    db.commit()
    return _profile_dict(profile)


# ---------- generic CRUD for target lists ----------

def _register_target_routes(prefix: str, model):
    @app.get(f"/{prefix}")
    def list_items(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
        items = db.query(model).filter(model.user_id == user_id).order_by(model.id).all()
        return [_named_dict(i) for i in items]

    @app.post(f"/{prefix}", status_code=201)
    def create_item(payload: NamedItemIn, user_id: int = Depends(get_current_user_id),
                    db: Session = Depends(get_db)):
        kwargs = {"user_id": user_id, "name": payload.name}
        if hasattr(model, "url"):
            kwargs["url"] = payload.url
        if hasattr(model, "notes"):
            kwargs["notes"] = payload.notes
        item = model(**kwargs)
        db.add(item)
        db.commit()
        db.refresh(item)
        return _named_dict(item)

    @app.patch(f"/{prefix}/{{item_id}}")
    def update_item(item_id: int, payload: NamedItemPatch,
                    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
        item = db.query(model).filter(model.id == item_id, model.user_id == user_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"{prefix} item not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            if hasattr(model, key):
                setattr(item, key, value)
        db.commit()
        return _named_dict(item)

    @app.delete(f"/{prefix}/{{item_id}}", status_code=204)
    def delete_item(item_id: int,
                    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
        item = db.query(model).filter(model.id == item_id, model.user_id == user_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"{prefix} item not found")
        db.delete(item)
        db.commit()
        return None


_register_target_routes("target-countries", TargetCountry)
_register_target_routes("target-career-sites", TargetCareerSite)
_register_target_routes("target-roles", TargetRole)


# ---------- preferences ----------

@app.get("/preferences")
def get_preferences(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    pref = db.get(UserPreference, user_id)
    return {"user_id": user_id, "language": pref.language if pref else None}


@app.put("/preferences")
def put_preferences(payload: PreferencesIn,
                    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    pref = db.get(UserPreference, user_id)
    if not pref:
        pref = UserPreference(user_id=user_id)
        db.add(pref)
    pref.language = payload.language
    db.commit()
    return {"user_id": user_id, "language": pref.language}


# ---------- internal endpoints ----------

@app.get("/internal/profiles")
def internal_profiles(user_id: int, active_only: bool = True, db: Session = Depends(get_db),
                      _: None = Depends(verify_internal_key)):
    query = db.query(UserProfile).filter(UserProfile.user_id == user_id,
                                         UserProfile.deleted_at.is_(None))
    if active_only:
        query = query.filter(UserProfile.is_active.is_(True))
    return [_profile_dict(p) for p in query.all()]


@app.get("/internal/profiles/status")
def internal_profile_status(profile_ids: str = "", db: Session = Depends(get_db),
                            _: None = Depends(verify_internal_key)):
    ids = [int(i) for i in profile_ids.split(",") if i.strip().isdigit()]
    rows = db.query(UserProfile).filter(UserProfile.id.in_(ids)).all() if ids else []
    return {str(p.id): {"is_active": p.is_active, "deleted_at": p.deleted_at is not None}
            for p in rows}


@app.get("/internal/profiles/{profile_id}")
def internal_profile(profile_id: int, db: Session = Depends(get_db),
                     _: None = Depends(verify_internal_key)):
    profile = db.get(UserProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _profile_dict(profile)


@app.post("/internal/users/{user_id}/seed-defaults", status_code=201)
def seed_defaults(user_id: int, db: Session = Depends(get_db),
                  _: None = Depends(verify_internal_key)):
    """Populate starter target lists for a newly registered user."""
    for name in DEFAULT_COUNTRIES:
        if not db.query(TargetCountry).filter_by(user_id=user_id, name=name).first():
            db.add(TargetCountry(user_id=user_id, name=name))
    for name in DEFAULT_SITES:
        if not db.query(TargetCareerSite).filter_by(user_id=user_id, name=name).first():
            db.add(TargetCareerSite(user_id=user_id, name=name))
    for name in DEFAULT_ROLES:
        if not db.query(TargetRole).filter_by(user_id=user_id, name=name).first():
            db.add(TargetRole(user_id=user_id, name=name))
    db.commit()
    return {"status": "seeded"}


@app.get("/internal/targets")
def internal_targets(user_id: int, db: Session = Depends(get_db),
                     _: None = Depends(verify_internal_key)):
    return {
        "countries": [_named_dict(i) for i in db.query(TargetCountry).filter_by(user_id=user_id).all()],
        "career_sites": [_named_dict(i) for i in db.query(TargetCareerSite).filter_by(user_id=user_id).all()],
        "roles": [_named_dict(i) for i in db.query(TargetRole).filter_by(user_id=user_id).all()],
    }


@app.get("/internal/users/{user_id}/preference")
def internal_preference(user_id: int, db: Session = Depends(get_db),
                        _: None = Depends(verify_internal_key)):
    pref = db.get(UserPreference, user_id)
    return {"user_id": user_id, "language": pref.language if pref else None}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
