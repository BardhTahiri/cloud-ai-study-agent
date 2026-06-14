from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings
from backend.app.db.models import Base, CourseRecord
from backend.app.models.entities import utc_now


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _ensure_sqlite_directory(url: str) -> None:
    if not url.startswith("sqlite:///"):
        return

    raw_path = url.removeprefix("sqlite:///")
    if raw_path == ":memory:":
        return

    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)


database_url = _normalize_database_url(settings.database_url)
_ensure_sqlite_directory(database_url)

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        _seed_default_course(db)


def _seed_default_course(db: Session) -> None:
    existing = db.execute(select(CourseRecord).limit(1)).scalar_one_or_none()
    if existing is not None:
        return

    db.add(
        CourseRecord(
            id=str(uuid4()),
            name="Cloud Computing",
            description="Demo course for the AI study agent workflow.",
            created_at=utc_now(),
        )
    )
    db.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
