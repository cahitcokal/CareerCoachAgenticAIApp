"""FastAPI dependencies for bearer-token auth and service-to-service calls."""
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from career_shared.config import get_settings
from career_shared.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


class AuthError(HTTPException):
    def __init__(self, detail="Authentication required"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> int:
    if credentials is None:
        raise AuthError()
    try:
        payload = decode_access_token(credentials.credentials)
        return int(payload["sub"])
    except Exception:
        raise AuthError("Invalid or expired token") from None


def verify_internal_key(x_internal_key: str | None = Header(default=None)) -> None:
    expected = get_settings().internal_api_key
    if not expected or x_internal_key != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
