"""Database utilities for the avatar pipeline."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from services.avatar_pipeline.config.settings import Settings


def create_engine_from_settings(settings: Settings) -> Engine:
    """Create a SQLAlchemy engine taking SQLite specifics into account."""

    connect_args = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(settings.database_url, future=True, echo=False, connect_args=connect_args)


def create_session_factory(settings: Settings) -> sessionmaker:
    """Create a session factory bound to the configured database."""

    engine = create_engine_from_settings(settings)
    return sessionmaker(bind=engine, expire_on_commit=False, class_=Session, future=True)


class Database:
    """Small helper class wrapping engine, session factory, and context manager."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.engine = create_engine_from_settings(settings)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False, class_=Session, future=True)

    def create_schema(self, base_metadata) -> None:
        base_metadata.create_all(self.engine)

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        session: Session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
