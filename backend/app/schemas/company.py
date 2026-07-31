from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationInfo, field_validator

from app.core.auth import Role, validate_password_policy


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    logo_url: str | None = None
    invoice_logo_url: str | None = None
    email: EmailStr | None = None
    website: str | None = None
    timezone: str
    language: str
    bin_tax_id: str | None = None
    currency: str
    invoice_prefix: str
    invoice_number_format: str
    next_invoice_number: int
    tax_percentage: Decimal
    footer_text: str | None = None
    payment_information: str | None = None
    notes: str | None = None
    address: str | None = None
    phone: str | None = None
    instagram: str | None = None
    director_name: str | None = None
    welcome_message: str | None = None
    receipt_signature: str | None = None
    created_at: datetime
    updated_at: datetime


class CompanyUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    website: str | None = None
    timezone: str | None = Field(default=None, min_length=2, max_length=64)
    language: str | None = Field(default=None, min_length=2, max_length=16)
    bin_tax_id: str | None = Field(default=None, min_length=3, max_length=32)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    address: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    logo_url: str | None = Field(default=None, max_length=512)
    invoice_logo_url: str | None = Field(default=None, max_length=512)
    invoice_prefix: str | None = Field(default=None, min_length=1, max_length=16)
    invoice_number_format: str | None = Field(default=None, min_length=3, max_length=64)
    tax_percentage: Decimal | None = Field(default=None, ge=0, le=100)
    footer_text: str | None = Field(default=None, max_length=500)
    payment_information: str | None = None
    notes: str | None = None
    instagram: str | None = Field(default=None, max_length=128)
    director_name: str | None = Field(default=None, max_length=120)
    welcome_message: str | None = None
    receipt_signature: str | None = None


class CompanyLogoResponse(BaseModel):
    url: str


class CompanyUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    email: EmailStr
    full_name: str | None = None
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class CompanyUsersResponse(BaseModel):
    items: list[CompanyUserRead]


class CompanyInviteRequest(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    role: Role

    @field_validator("role")
    @classmethod
    def prevent_owner_invites(cls, value: Role) -> Role:
        if value is Role.OWNER:
            raise ValueError("Company owners are created during registration")
        return value


class CompanyUserRoleUpdateRequest(BaseModel):
    role: Role


class CompanyInvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    email: EmailStr
    full_name: str | None = None
    role: Role
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CompanyInvitationCreateResponse(BaseModel):
    invitation: CompanyInvitationRead
    invite_token: str


class CompanyInvitationsResponse(BaseModel):
    items: list[CompanyInvitationRead]


class CompanyInvitationAcceptRequest(BaseModel):
    token: str = Field(min_length=32)
    full_name: str = Field(min_length=2, max_length=120)
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
