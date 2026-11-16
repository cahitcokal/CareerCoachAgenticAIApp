"""Identity provider abstraction.

The system ships with a local provider (bcrypt + users table, implemented in
the user-management service). An external provider such as Supabase can be
enabled with IDP_PROVIDER without changing callers: the interface is minimal.
"""
import os
from typing import Protocol


class IdentityProvider(Protocol):
    name: str

    def authenticate(self, email: str, password: str) -> dict | None: ...

    def register(self, email: str, password: str, full_name: str) -> dict: ...

    def get_user(self, user_id: int) -> dict | None: ...


def get_identity_provider_name() -> str:
    return os.getenv("IDP_PROVIDER", "local")
