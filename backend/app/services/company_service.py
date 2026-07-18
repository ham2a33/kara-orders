from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from secrets import token_urlsafe

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.core.auth import Role
from app.core.config import Settings
from app.core.exceptions import ConfigurationError, ConflictError, ForbiddenError, NotFoundError
from app.core.security import hash_password
from app.db.models.company import Company
from app.db.models.company_invitation import CompanyInvitation
from app.db.models.user import User
from app.repositories.company_invitation_repository import CompanyInvitationRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
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
    CompanyUsersResponse,
)
from app.services.platform_service import PlatformService
from app.services.storage_service import StorageService, build_storage_object_name


@dataclass(frozen=True)
class InvitationTokenBundle:
    invitation: CompanyInvitation
    raw_token: str


class CompanyService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        storage_service: StorageService | None = None,
    ) -> None:
        self.session = session
        self.settings = settings
        self.storage = storage_service
        self.companies = CompanyRepository(session)
        self.users = UserRepository(session)
        self.invitations = CompanyInvitationRepository(session)

    def get_profile(self, company: Company) -> CompanyRead:
        return CompanyRead.model_validate(company)

    def update_profile(self, company: Company, payload: CompanyUpdateRequest) -> CompanyRead:
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            if field == "currency" and value is not None:
                setattr(company, field, str(value).upper())
            elif field == "timezone" and value is not None:
                setattr(company, field, str(value))
            elif field == "language" and value is not None:
                setattr(company, field, str(value).lower())
            elif field == "tax_percentage" and value is not None:
                setattr(company, field, Decimal(str(value)))
            else:
                setattr(company, field, value)

        self.session.commit()
        self.session.refresh(company)
        PlatformService(self.session).log_action(
            action="company_updated",
            company_id=company.id,
            actor_user_id=None,
            resource_type="company",
            resource_id=str(company.id),
            description="Company profile updated",
            metadata=updates,
        )
        return CompanyRead.model_validate(company)

    def upload_logo(
        self,
        company: Company,
        *,
        content: bytes,
        content_type: str,
        kind: str,
    ) -> CompanyLogoResponse:
        if self.storage is None:
            raise ConfigurationError("Storage service is not available")

        suffix = "png"
        if "jpeg" in content_type or "jpg" in content_type:
            suffix = "jpg"
        object_path = build_storage_object_name(
            "companies",
            str(company.id),
            kind,
            str(int(datetime.now(UTC).timestamp())),
            suffix=suffix,
        )
        result = self.storage.upload_public_file(
            bucket=self.settings.supabase_storage_bucket,
            object_path=object_path,
            content=content,
            content_type=content_type,
        )
        if kind == "logo":
            company.logo_url = result.public_url
        else:
            company.invoice_logo_url = result.public_url
        PlatformService(self.session).record_storage_usage(company.id, len(content))
        self.session.commit()
        PlatformService(self.session).log_action(
            action="company_logo_uploaded",
            company_id=company.id,
            actor_user_id=None,
            resource_type="company",
            resource_id=str(company.id),
            description=f"{kind} uploaded",
            metadata={"kind": kind, "content_type": content_type},
        )
        return CompanyLogoResponse(url=result.public_url)

    def list_users(self, company: Company) -> CompanyUsersResponse:
        users = self.users.list_by_company(company.id)
        return CompanyUsersResponse(items=[CompanyUserRead.model_validate(user) for user in users])

    def invite_user(
        self,
        company: Company,
        inviter: User,
        payload: CompanyInviteRequest,
    ) -> CompanyInvitationCreateResponse:
        platform = PlatformService(self.session)
        current_users = self.session.scalar(
            sa.select(sa.func.count(User.id)).where(
                User.company_id == company.id,
                User.deleted_at.is_(None),
                User.is_active.is_(True),
            )
        ) or 0
        platform.ensure_limit(company.id, "maximum_users", 1, current=int(current_users))
        existing_user = self.users.get_any_by_email(payload.email)
        if existing_user is not None:
            raise ConflictError("A user with this email already exists in the company")

        pending_invite = self.session.scalar(
            sa.select(CompanyInvitation).where(
                CompanyInvitation.company_id == company.id,
                CompanyInvitation.email == payload.email,
                CompanyInvitation.deleted_at.is_(None),
                CompanyInvitation.accepted_at.is_(None),
            )
        )
        if pending_invite is not None:
            raise ConflictError("An invitation for this email already exists")

        raw_token = token_urlsafe(32)
        invitation = CompanyInvitation(
            company_id=company.id,
            email=payload.email,
            full_name=payload.full_name,
            role=payload.role.value,
            token_hash=self._hash_token(raw_token),
            invited_by_id=inviter.id,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        self.session.add(invitation)
        self.session.commit()
        self.session.refresh(invitation)
        platform.log_action(
            action="user_invited",
            company_id=company.id,
            actor_user_id=inviter.id,
            resource_type="company_invitation",
            resource_id=str(invitation.id),
            description="Company user invited",
            metadata={"email": payload.email, "role": payload.role.value},
        )

        return CompanyInvitationCreateResponse(
            invitation=CompanyInvitationRead.model_validate(invitation),
            invite_token=raw_token,
        )

    def list_invitations(self, company: Company) -> CompanyInvitationsResponse:
        invitations = self.invitations.get_pending_by_company(company.id)
        return CompanyInvitationsResponse(
            items=[CompanyInvitationRead.model_validate(invitation) for invitation in invitations]
        )

    def change_user_role(self, company: Company, current_user: User, target_user: User, role: Role) -> CompanyUserRead:
        if target_user.company_id != company.id:
            raise ForbiddenError("You cannot manage users from another company")
        if target_user.role == Role.OWNER.value:
            raise ForbiddenError("The owner role cannot be changed")
        if target_user.id == current_user.id and role.value != current_user.role:
            raise ForbiddenError("You cannot change your own role")
        target_user.role = role.value
        self.session.commit()
        self.session.refresh(target_user)
        PlatformService(self.session).log_action(
            action="role_changed",
            company_id=company.id,
            actor_user_id=current_user.id,
            resource_type="user",
            resource_id=str(target_user.id),
            description="User role changed",
            metadata={"role": role.value},
        )
        return CompanyUserRead.model_validate(target_user)

    def remove_user(self, company: Company, current_user: User, target_user: User) -> None:
        if target_user.company_id != company.id:
            raise ForbiddenError("You cannot manage users from another company")
        if target_user.id == current_user.id:
            raise ForbiddenError("You cannot remove yourself")
        if target_user.role == Role.OWNER.value:
            raise ForbiddenError("The owner cannot be removed")
        target_user.is_active = False
        target_user.deleted_at = datetime.now(UTC)
        self.session.commit()
        PlatformService(self.session).log_action(
            action="user_removed",
            company_id=company.id,
            actor_user_id=current_user.id,
            resource_type="user",
            resource_id=str(target_user.id),
            description="User removed from company",
        )

    def accept_invitation(self, payload: CompanyInvitationAcceptRequest) -> CompanyUserRead:
        token_hash = self._hash_token(payload.token)
        invitation = self.invitations.get_by_token_hash(token_hash)
        if (
            invitation is None
            or invitation.deleted_at is not None
            or invitation.accepted_at is not None
            or invitation.expires_at < datetime.now(UTC)
        ):
            raise NotFoundError("Invitation not found or expired")

        existing_user = self.users.get_any_by_email(invitation.email)
        if existing_user is not None:
            raise ConflictError("A user with this email already exists")

        user = User(
            company_id=invitation.company_id,
            email=invitation.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            role=invitation.role,
            is_active=True,
        )
        invitation.accepted_at = datetime.now(UTC)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        PlatformService(self.session).get_or_create_default_subscription(user.company)
        PlatformService(self.session).log_action(
            action="invitation_accepted",
            company_id=user.company_id,
            actor_user_id=user.id,
            resource_type="company_invitation",
            resource_id=str(invitation.id),
            description="Invitation accepted",
        )
        return CompanyUserRead.model_validate(user)

    @staticmethod
    def _hash_token(value: str) -> str:
        return sha256(value.encode("utf-8")).hexdigest()
