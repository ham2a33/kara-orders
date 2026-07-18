from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationInfo, field_validator

from app.core.auth import Role, validate_password_policy
from app.schemas.company import CompanyRead


class AuthUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    email: EmailStr
    full_name: str | None = None
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RegisterRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=120)
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    confirm_password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        validate_password_policy(value)
        return value

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, value: str, info: ValidationInfo) -> str:
        password = info.data.get("password")
        if password is not None and value != password:
            raise ValueError("Passwords do not match")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class AuthTokens(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(AuthTokens):
    model_config = ConfigDict(from_attributes=True)

    user: AuthUserRead
    company: CompanyRead


class LogoutResponse(BaseModel):
    detail: str


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: AuthUserRead
    company: CompanyRead
