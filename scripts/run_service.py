"""Run one CareerCoach FastAPI service from an IDE or a terminal.

This project-level entry point keeps PyCharm run configurations small and
portable. Set DATABASE_URL in the run configuration to use PostgreSQL,
Supabase, Neon, or another SQLAlchemy-compatible database; otherwise each
service gets a local SQLite file under runtime/.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import uvicorn


ROOT = Path(__file__).resolve().parents[1]
SERVICES = {
    "user-management": (8001, "career_users"),
    "personal-admin": (8002, "career_personal"),
    "system-admin": (8003, "career_system"),
    "opportunity-service": (8004, "career_opportunities"),
    "scout-agent": (8005, "scout"),
    "relocation-agent": (8006, "relocation"),
    "application-coach-agent": (8007, "application_coach"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a CareerCoach service")
    parser.add_argument("service", choices=sorted(SERVICES))
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int)
    parser.add_argument("--reload", action="store_true")
    return parser.parse_args()


def configure_environment(service: str, database_name: str) -> int:
    port = SERVICES[service][0]
    service_dir = ROOT / "services" / service
    runtime_dir = ROOT / "runtime"
    runtime_dir.mkdir(exist_ok=True)

    # Make imports work from PyCharm, the project root, and CI alike.
    sys.path.insert(0, str(service_dir))
    sys.path.insert(0, str(ROOT / "services" / "shared"))
    os.environ.setdefault("PYTHONPATH", os.pathsep.join(
        [str(service_dir), str(ROOT / "services" / "shared")]
    ))

    sqlite_path = (runtime_dir / f"{database_name}.db").as_posix()
    os.environ.setdefault("DATABASE_PROVIDER", "sqlite")
    os.environ.setdefault("SQLITE_PATH", sqlite_path)
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{sqlite_path}")
    os.environ.setdefault("JWT_SECRET", "dev-only-change-me-please-32chars-min")
    os.environ.setdefault("INTERNAL_API_KEY", "dev-internal-key")
    os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
    return int(os.getenv("PORT", port))


def main() -> None:
    args = parse_args()
    port = configure_environment(args.service, SERVICES[args.service][1])
    if args.port is not None:
        port = args.port
    os.environ["PORT"] = str(port)
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=port,
        reload=args.reload,
        app_dir=str(ROOT / "services" / args.service),
    )


if __name__ == "__main__":
    main()
