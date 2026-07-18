from __future__ import annotations

from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.auth import Role, has_minimum_role
from app.core.config import Settings
from app.core.exceptions import ConfigurationError, ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.models.user import User
from app.dependencies.deps import get_app_settings, get_db
from app.services.platform_service import PlatformService

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing access token")

    payload = decode_token(credentials.credentials, settings, expected_type="access")
    try:
        user_id = UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Invalid access token") from exc

    user = session.get(User, user_id)
    if user is None or user.deleted_at is not None or not user.is_active:
        raise UnauthorizedError("User is inactive or does not exist")

    if user.company.deleted_at is not None:
        raise UnauthorizedError("Company is inactive")

    if str(payload.get("company_id")) != str(user.company_id) or str(payload.get("role")) != user.role:
        raise UnauthorizedError("Access token no longer matches the user state")

    system_settings = PlatformService(session).get_system_settings()
    if system_settings.maintenance_mode and not user.is_super_admin:
        raise ConfigurationError("Maintenance mode is enabled")

    return user


def get_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def require_roles(*required_roles: Role):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not has_minimum_role(current_user.role, list(required_roles)):
            raise ForbiddenError("You do not have permission to access this resource")
        return current_user

    return dependency


def require_company_access(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
) -> User:
    if str(current_user.company_id) != str(company_id):
        raise ForbiddenError("You do not have permission to access this company")
    return current_user


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_super_admin:
        raise ForbiddenError("You do not have permission to access this resource")
    return current_user
