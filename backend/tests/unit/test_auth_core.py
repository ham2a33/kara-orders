from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.auth import Role, has_minimum_role, validate_password_policy
from app.core.config import Settings
from app.core.security import (
    create_access_token_with_claims,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_policy_accepts_strong_password() -> None:
    validate_password_policy("Password123!")


def test_password_policy_rejects_weak_password() -> None:
    with pytest.raises(ValueError):
        validate_password_policy("weakpass")


def test_password_hash_round_trip() -> None:
    password_hash = hash_password("Password123!")
    assert verify_password("Password123!", password_hash) is True
    assert verify_password("Different123!", password_hash) is False


def test_access_token_contains_claims() -> None:
    settings = Settings(database_url="postgresql+psycopg://example")
    token = create_access_token_with_claims(
        subject="user-id",
        settings=settings,
        extra_claims={"company_id": "company-id", "role": Role.ADMIN.value},
    )

    payload = decode_token(token, settings, expected_type="access")
    assert payload["sub"] == "user-id"
    assert payload["company_id"] == "company-id"
    assert payload["role"] == Role.ADMIN.value
    assert payload["type"] == "access"


def test_role_hierarchy() -> None:
    assert has_minimum_role(Role.OWNER, [Role.ADMIN]) is True
    assert has_minimum_role(Role.ADMIN, [Role.ADMIN]) is True
    assert has_minimum_role(Role.MANAGER, [Role.ADMIN]) is False
    assert has_minimum_role(Role.EMPLOYEE, [Role.MANAGER]) is False


def test_production_settings_require_strong_secret() -> None:
    with pytest.raises(ValueError):
        Settings(database_url="postgresql+psycopg://example", environment="production")


def test_production_settings_normalize_cookie_security() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://example",
        environment="production",
        secret_key="x" * 32,
    )

    assert settings.auth_refresh_cookie_secure is True
    assert settings.auth_refresh_cookie_samesite == "strict"
