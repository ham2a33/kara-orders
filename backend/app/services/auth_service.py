from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.auth import Role, validate_password_policy
from app.core.config import Settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token_with_claims,
    create_refresh_token_with_claims,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models.company import Company
from app.db.models.user import User
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, MeResponse, RegisterRequest
from app.services.platform_service import PlatformService


@dataclass(frozen=True)
class TokenBundle:
    access_token: str
    refresh_token: str
    expires_in: int


class AuthService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.users = UserRepository(session)
        self.companies = CompanyRepository(session)

    def register(self, payload: RegisterRequest) -> tuple[AuthResponse, str]:
        validate_password_policy(payload.password)
        if self.users.get_any_by_email(payload.email):
            raise ConflictError("A user with this email already exists")

        company = Company(
            name=payload.company_name,
            currency="KZT",
            invoice_prefix="INV",
        )
        user = User(
            company=company,
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            role=Role.OWNER.value,
            is_active=True,
        )

        self.session.add(company)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(company)
        self.session.refresh(user)
        PlatformService(self.session).get_or_create_default_subscription(company)
        PlatformService(self.session).log_action(
            action="company_created",
            company_id=company.id,
            actor_user_id=user.id,
            resource_type="company",
            resource_id=str(company.id),
            description="Company registered",
        )

        tokens = self._build_tokens(user)
        return self._build_auth_response(user, company, tokens), tokens.refresh_token

    def login(self, payload: LoginRequest) -> tuple[AuthResponse, str]:
        user = self.users.get_by_email(payload.email)
        if user is None or user.deleted_at is not None or not user.is_active:
            raise UnauthorizedError("Invalid email or password")
        if not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        PlatformService(self.session).log_action(
            action="login",
            company_id=user.company_id,
            actor_user_id=user.id,
            resource_type="auth",
            resource_id=str(user.id),
            description="User logged in",
        )

        return self._issue_token_response(user)

    def refresh(self, refresh_token: str) -> tuple[AuthResponse, str]:
        payload = decode_token(refresh_token, self.settings, expected_type="refresh")
        user = self._load_user_from_claims(payload)
        return self._issue_token_response(user)

    def get_profile(self, user: User) -> MeResponse:
        return MeResponse(user=user, company=user.company)

    def _issue_token_response(self, user: User) -> tuple[AuthResponse, str]:
        tokens = self._build_tokens(user)
        return self._build_auth_response(user, user.company, tokens), tokens.refresh_token

    def _build_tokens(self, user: User) -> TokenBundle:
        claims = {
            "company_id": str(user.company_id),
            "role": user.role,
        }
        access_token = create_access_token_with_claims(
            subject=str(user.id),
            settings=self.settings,
            extra_claims=claims,
        )
        refresh_token = create_refresh_token_with_claims(
            subject=str(user.id),
            settings=self.settings,
            extra_claims=claims,
        )
        return TokenBundle(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.settings.access_token_expire_minutes * 60,
        )

    def _load_user_from_claims(self, payload: dict[str, object]) -> User:
        try:
            user_id = UUID(str(payload["sub"]))
        except (KeyError, ValueError) as exc:
            raise UnauthorizedError("Invalid token payload") from exc

        user = self.users.get_active_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User is inactive or does not exist")

        company_id = str(payload.get("company_id"))
        role = str(payload.get("role"))
        if company_id != str(user.company_id) or role != user.role:
            raise UnauthorizedError("Token no longer matches the user state")

        if user.company.deleted_at is not None:
            raise UnauthorizedError("Company is inactive")

        return user

    def _build_auth_response(self, user: User, company: Company, tokens: TokenBundle) -> AuthResponse:
        return AuthResponse(
            access_token=tokens.access_token,
            token_type="bearer",
            expires_in=tokens.expires_in,
            user=user,
            company=company,
        )
