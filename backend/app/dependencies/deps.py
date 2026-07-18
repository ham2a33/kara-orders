from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db_session


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()


def get_app_settings() -> Settings:
    return get_settings()
