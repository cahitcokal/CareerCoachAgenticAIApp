"""Thin service-to-service HTTP client.

Attaches the internal API key for service calls and forwards the caller's
bearer token when a user context is required.
"""
import httpx

from career_shared.config import get_settings


def internal_headers(token: str | None = None) -> dict:
    headers = {"X-Internal-Key": get_settings().internal_api_key}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


class ServiceClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self, method: str, path: str, *, token: str | None = None, **kwargs):
        headers = {**internal_headers(token), **kwargs.pop("headers", {})}
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            return client.request(method, path, headers=headers, **kwargs)

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.request("DELETE", path, **kwargs)
