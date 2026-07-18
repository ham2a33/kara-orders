from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationError
from app.services.storage_service import StorageService, SupabaseStorageService


@lru_cache(maxsize=1)
def get_storage_settings() -> Settings:
    return get_settings()


def get_storage_service() -> StorageService:
    return SupabaseStorageService(get_storage_settings())


def get_optional_storage_service() -> StorageService | None:
    try:
        return get_storage_service()
    except ConfigurationError:
        return None
