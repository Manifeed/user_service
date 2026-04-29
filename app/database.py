from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "40"))
DB_POOL_TIMEOUT_SECONDS = int(os.getenv("DB_POOL_TIMEOUT_SECONDS", "30"))
DB_POOL_RECYCLE_SECONDS = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800"))

DEFAULT_IDENTITY_DATABASE_URL = "postgresql://manifeed:manifeed@localhost:5432/manifeed_identity"


def _resolve_database_url() -> str:
    database_url = os.getenv("IDENTITY_DATABASE_URL")
    if not database_url:
        if _requires_explicit_database_url():
            raise RuntimeError("IDENTITY_DATABASE_URL must be configured outside local/test environments")
        database_url = DEFAULT_IDENTITY_DATABASE_URL
    if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def _requires_explicit_database_url() -> bool:
    raw_value = os.getenv("REQUIRE_EXPLICIT_DATABASE_URLS")
    if raw_value is not None:
        return raw_value.strip().lower() in {"1", "true", "yes", "on"}
    environment = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "")).strip().lower()
    return environment in {"prod", "production", "staging"}


def _create_engine(database_url: str):
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_timeout=DB_POOL_TIMEOUT_SECONDS,
        pool_recycle=DB_POOL_RECYCLE_SECONDS,
    )


IDENTITY_DATABASE_URL = _resolve_database_url()
identity_engine = _create_engine(IDENTITY_DATABASE_URL)
IdentitySessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=identity_engine)


def open_identity_db_session() -> Session:
    return IdentitySessionLocal()


def get_identity_db_session() -> Generator[Session, None, None]:
    db = open_identity_db_session()
    try:
        yield db
    finally:
        db.close()
