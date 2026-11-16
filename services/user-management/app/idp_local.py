"""Local identity provider: bcrypt + users table.

Selected when IDP_PROVIDER=local (default). A Supabase implementation can be
added behind the same IdentityProvider interface without touching routes.
"""
import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import PasswordResetToken, SystemAdmin, User
from career_shared.security import get_password_hash, verify_password


class LocalIdentityProvider:
    name = "local"

    def authenticate(self, db: Session, email: str, password: str) -> User | None:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user or not user.is_active or not verify_password(password, user.hashed_password):
            return None
        return user

    def register(self, db: Session, email: str, password: str, full_name: str) -> User:
        user = User(
            email=email.strip().lower(),
            full_name=full_name.strip(),
            hashed_password=get_password_hash(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_user(self, db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)

    def is_system_admin(self, db: Session, user_id: int) -> bool:
        return db.get(SystemAdmin, user_id) is not None

    def create_reset_token(self, db: Session, user_id: int, ttl_minutes: int = 30) -> str:
        token = secrets.token_urlsafe(32)
        db.add(PasswordResetToken(
            user_id=user_id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
        ))
        db.commit()
        return token

    def consume_reset_token(self, db: Session, token: str, new_password: str) -> bool:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        record = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.token_hash == token_hash,
                    PasswordResetToken.used == False,  # noqa: E712
                    PasswordResetToken.expires_at > datetime.utcnow())
            .first()
        )
        if not record:
            return False
        user = db.get(User, record.user_id)
        if not user:
            return False
        user.hashed_password = get_password_hash(new_password)
        record.used = True
        db.commit()
        return True
