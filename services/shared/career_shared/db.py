"""Shared SQLAlchemy engine/session boundary for every microservice.

Switching databases requires changing DATABASE_URL, not changing models,
repositories, or endpoint code.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from career_shared.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        url = get_settings().resolved_database_url()
        engine_options = {"pool_pre_ping": True}
        if url.startswith("sqlite"):
            # FastAPI requests and tests can use different threads.
            engine_options["connect_args"] = {"check_same_thread": False}
        _engine = create_engine(url, **engine_options)
    return _engine


def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _SessionLocal


def get_db():
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=get_engine())


def dispose_engine():
    """Dispose the current pool so a process can switch URLs safely."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
