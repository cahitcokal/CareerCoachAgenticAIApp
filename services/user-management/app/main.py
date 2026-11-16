"""User Management Service: auth, registration, password flows, admin user CRUD.

Owns the users / system_admins / password_reset_tokens tables. Issues JWT
bearer tokens consumed by every other service.
"""
import os

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.idp_local import LocalIdentityProvider
from app.models import SystemAdmin, User
from career_shared.auth import get_current_user_id, verify_internal_key
from career_shared.client import ServiceClient
from career_shared.config import get_settings
from career_shared.cors import add_cors
from career_shared.db import get_db, init_db
from career_shared.security import create_access_token, verify_password, get_password_hash

app = FastAPI(title="User Management Service")
add_cors(app)
idp = LocalIdentityProvider()
_personal_admin = ServiceClient(get_settings().personal_admin_url)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "user-management"}


# ---------- schemas ----------

class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UpdateMeRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=150)
    email: EmailStr | None = None


class AdminCreateUserRequest(RegisterRequest):
    is_system_admin: bool = False


class AdminUpdateUserRequest(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None
    is_system_admin: bool | None = None


def _user_dict(user: User, db: Session) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_system_admin": idp.is_system_admin(db, user.id),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _require_admin(user_id: int, db: Session) -> User:
    user = db.get(User, user_id)
    if not user or not idp.is_system_admin(db, user_id):
        raise HTTPException(status_code=403, detail="System administrator access required")
    return user


# ---------- public auth endpoints ----------

@app.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = idp.register(db, email, payload.password, payload.full_name)
    # Seed default targets in personal-admin (best effort).
    try:
        _personal_admin.post(f"/internal/users/{user.id}/seed-defaults")
    except Exception:
        pass
    return TokenResponse(access_token=create_access_token(user.id), user=_user_dict(user, db))


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = idp.authenticate(db, str(payload.email).lower(), payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id), user=_user_dict(user, db))


@app.post("/auth/logout", status_code=204)
def logout():
    # JWT is stateless; clients discard the token. Kept for API symmetry.
    return None


@app.post("/auth/forgot-password", status_code=202)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(payload.email).lower()).first()
    if user:
        token = idp.create_reset_token(db, user.id)
        # TODO(email): deliver via SMTP. In development the token is logged only.
        print(f"[user-management] password reset token for user {user.id}: {token}")
    return {"detail": "If the account exists, a reset link has been sent."}


@app.post("/auth/reset-password", status_code=204)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    if not idp.consume_reset_token(db, payload.token, payload.new_password):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return None


@app.get("/auth/me")
def me(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Account unavailable")
    return _user_dict(user, db)


@app.patch("/auth/me")
def update_me(payload: UpdateMeRequest, user_id: int = Depends(get_current_user_id),
              db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.email is not None:
        email = str(payload.email).lower()
        conflict = db.query(User).filter(User.email == email, User.id != user.id).first()
        if conflict:
            raise HTTPException(status_code=409, detail="Email already in use")
        user.email = email
    db.commit()
    return _user_dict(user, db)


@app.post("/auth/change-password", status_code=204)
def change_password(payload: ChangePasswordRequest,
                    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user or not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return None


# ---------- admin endpoints (system admin role required) ----------

@app.get("/admin/users")
def admin_list_users(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    users = db.query(User).order_by(User.id).all()
    return [_user_dict(u, db) for u in users]


@app.post("/admin/users", status_code=201)
def admin_create_user(payload: AdminCreateUserRequest,
                      user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = idp.register(db, email, payload.password, payload.full_name)
    if payload.is_system_admin:
        db.add(SystemAdmin(user_id=user.id))
        db.commit()
    return _user_dict(user, db)


@app.patch("/admin/users/{target_id}")
def admin_update_user(target_id: int, payload: AdminUpdateUserRequest,
                      user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    _require_admin(user_id, db)
    user = db.get(User, target_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.is_system_admin is not None:
        existing = db.get(SystemAdmin, target_id)
        if payload.is_system_admin and not existing:
            db.add(SystemAdmin(user_id=target_id))
        elif not payload.is_system_admin and existing:
            db.delete(existing)
    db.commit()
    return _user_dict(user, db)


# ---------- internal endpoints (service-to-service) ----------

@app.get("/internal/users/{user_id}")
def internal_get_user(user_id: int, db: Session = Depends(get_db),
                      _: None = Depends(verify_internal_key)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_dict(user, db)


@app.get("/internal/users")
def internal_list_users(ids: str = "", db: Session = Depends(get_db),
                        _: None = Depends(verify_internal_key)):
    query = db.query(User)
    if ids:
        id_list = [int(i) for i in ids.split(",") if i.strip().isdigit()]
        query = query.filter(User.id.in_(id_list))
    return [_user_dict(u, db) for u in query.all()]


@app.get("/internal/users/{user_id}/is-system-admin")
def internal_is_system_admin(user_id: int, db: Session = Depends(get_db),
                             _: None = Depends(verify_internal_key)):
    return {"user_id": user_id, "is_system_admin": idp.is_system_admin(db, user_id)}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
