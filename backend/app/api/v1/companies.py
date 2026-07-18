from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import Role
from app.core.config import Settings
from app.core.exceptions import NotFoundError
from app.dependencies.auth import get_current_user, require_roles
from app.dependencies.deps import get_app_settings, get_db
from app.dependencies.storage import get_storage_service
from app.db.models.user import User
from app.schemas.company import (
    CompanyInviteRequest,
    CompanyInvitationAcceptRequest,
    CompanyInvitationCreateResponse,
    CompanyInvitationRead,
    CompanyInvitationsResponse,
    CompanyLogoResponse,
    CompanyRead,
    CompanyUpdateRequest,
    CompanyUserRead,
    CompanyUserRoleUpdateRequest,
    CompanyUsersResponse,
)
from app.services.company_service import CompanyService
from app.services.storage_service import StorageService
from app.services.platform_service import PlatformService
from app.utils.validators import validate_upload

router = APIRouter(prefix="/companies", tags=["companies"])


def _service(
    session: Session,
    settings: Settings,
    storage: StorageService | None = None,
) -> CompanyService:
    return CompanyService(session=session, settings=settings, storage_service=storage)


@router.get("/me", response_model=CompanyRead)
def get_my_company(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> CompanyRead:
    return _service(session, settings).get_profile(current_user.company)


@router.patch("/me", response_model=CompanyRead, dependencies=[Depends(require_roles(Role.ADMIN))])
def update_my_company(
    payload: CompanyUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> CompanyRead:
    return _service(session, settings).update_profile(current_user.company, payload)


@router.post("/me/logo", response_model=CompanyLogoResponse, dependencies=[Depends(require_roles(Role.ADMIN))])
def upload_company_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    storage: StorageService = Depends(get_storage_service),
) -> CompanyLogoResponse:
    content = file.file.read()
    system_settings = PlatformService(session).get_system_settings()
    validate_upload(
        content=content,
        filename=file.filename or "logo.png",
        content_type=file.content_type or "application/octet-stream",
        max_upload_size_mb=system_settings.max_upload_size_mb,
        allowed_file_types=system_settings.allowed_file_types,
        allowed_mime_types={"image/png", "image/jpeg", "image/webp", "image/svg+xml"},
    )
    return _service(session, settings, storage).upload_logo(
        current_user.company,
        content=content,
        content_type=file.content_type or "application/octet-stream",
        kind="logo",
    )


@router.post(
    "/me/invoice-logo",
    response_model=CompanyLogoResponse,
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
def upload_invoice_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    storage: StorageService = Depends(get_storage_service),
) -> CompanyLogoResponse:
    content = file.file.read()
    system_settings = PlatformService(session).get_system_settings()
    validate_upload(
        content=content,
        filename=file.filename or "invoice-logo.png",
        content_type=file.content_type or "application/octet-stream",
        max_upload_size_mb=system_settings.max_upload_size_mb,
        allowed_file_types=system_settings.allowed_file_types,
        allowed_mime_types={"image/png", "image/jpeg", "image/webp", "image/svg+xml"},
    )
    return _service(session, settings, storage).upload_logo(
        current_user.company,
        content=content,
        content_type=file.content_type or "application/octet-stream",
        kind="invoice-logo",
    )


@router.get("/me/users", response_model=CompanyUsersResponse, dependencies=[Depends(require_roles(Role.ADMIN))])
def list_company_users(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> CompanyUsersResponse:
    return _service(session, settings).list_users(current_user.company)


@router.post(
    "/me/users/invitations",
    response_model=CompanyInvitationCreateResponse,
    status_code=201,
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
def invite_company_user(
    payload: CompanyInviteRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> CompanyInvitationCreateResponse:
    return _service(session, settings).invite_user(current_user.company, current_user, payload)


@router.get(
    "/me/users/invitations",
    response_model=CompanyInvitationsResponse,
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
def list_company_invitations(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> CompanyInvitationsResponse:
    return _service(session, settings).list_invitations(current_user.company)


@router.patch(
    "/me/users/{user_id}/role",
    response_model=CompanyUserRead,
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
def change_company_user_role(
    user_id: UUID,
    payload: CompanyUserRoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> CompanyUserRead:
    service = _service(session, settings)
    target_user = service.users.get_by_id_and_company(user_id, current_user.company_id)
    if target_user is None:
        raise NotFoundError("User not found")
    return service.change_user_role(current_user.company, current_user, target_user, payload.role)


@router.delete(
    "/me/users/{user_id}",
    status_code=200,
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
def remove_company_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> None:
    service = _service(session, settings)
    target_user = service.users.get_by_id_and_company(user_id, current_user.company_id)
    if target_user is None:
        raise NotFoundError("User not found")
    service.remove_user(current_user.company, current_user, target_user)
    return {"detail": "User removed"}


@router.post("/invitations/accept", response_model=CompanyUserRead)
def accept_company_invitation(
    payload: CompanyInvitationAcceptRequest,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> CompanyUserRead:
    return _service(session, settings).accept_invitation(payload)
