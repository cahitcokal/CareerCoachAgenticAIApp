"""CORS setup so the SPA can call services directly from the browser."""
from fastapi.middleware.cors import CORSMiddleware

from career_shared.config import get_settings


def add_cors(app) -> None:
    origins = [o.strip() for o in get_settings().frontend_url.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
