from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.dependencies.deps import get_app_settings, get_db
from app.dependencies.storage import get_optional_storage_service
from app.services.ai.service import AIService
from app.services.storage_service import StorageService


def get_ai_service(
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    storage: StorageService | None = Depends(get_optional_storage_service),
) -> AIService:
    return AIService(session=session, settings=settings, storage_service=storage)
