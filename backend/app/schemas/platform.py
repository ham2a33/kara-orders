from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


SubscriptionStatus = Literal["trialing", "active", "past_due", "suspended", "expired", "canceled", "lifetime", "custom"]
NotificationStatus = Literal["unread", "read", "archived"]


class PlanLimitsRead(BaseModel):
    maximum_users: int | None = None
    maximum_products: int | None = None
    maximum_ai_requests: int | None = None
    maximum_storage_bytes: int | None = None
    maximum_companies: int | None = None
    maximum_orders_per_month: int | None = None


class SubscriptionPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    description: str | None = None
    currency: str
    price_monthly: Decimal
    setup_fee_amount: Decimal
    billing_cycle: str
    is_default: bool
    is_active: bool
    features: dict[str, Any]
    limits: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CompanySubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    plan: SubscriptionPlanRead
    status: SubscriptionStatus
    trial_end: datetime | None = None
    subscription_start: datetime | None = None
    subscription_end: datetime | None = None
    billing_disabled: bool
    setup_fee_paid: bool
    setup_fee_amount: Decimal
    setup_fee_paid_at: datetime | None = None
    period_start: datetime
    ai_requests_monthly: int
    ai_tokens_monthly: int
    ai_estimated_cost_monthly: Decimal
    recognition_count_monthly: int
    average_recognition_time_ms: Decimal
    storage_usage_bytes: int
    extra: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CompanyUsageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    period_start: datetime
    period_end: datetime | None = None
    monthly_ai_requests: int
    monthly_token_usage: int
    estimated_ai_cost: Decimal
    recognition_count: int
    average_recognition_time_ms: Decimal
    storage_usage_bytes: int
    created_at: datetime
    updated_at: datetime


class SubscriptionOverviewResponse(BaseModel):
    subscription: CompanySubscriptionRead
    usage: CompanyUsageRead
    limits: PlanLimitsRead


class UsageUpdateRead(BaseModel):
    monthly_ai_requests: int
    monthly_token_usage: int
    estimated_ai_cost: Decimal
    recognition_count: int
    average_recognition_time_ms: Decimal
    storage_usage_bytes: int


class SystemSettingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ai_enabled: bool
    maintenance_mode: bool
    max_upload_size_mb: int
    allowed_file_types: list[str]
    default_currency: str
    default_tax: Decimal
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class SystemSettingUpdateRequest(BaseModel):
    ai_enabled: bool | None = None
    maintenance_mode: bool | None = None
    max_upload_size_mb: int | None = Field(default=None, ge=0)
    allowed_file_types: list[str] | None = None
    default_currency: str | None = Field(default=None, min_length=3, max_length=3)
    default_tax: Decimal | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID | None = None
    actor_user_id: UUID | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    description: str | None = None
    event_metadata: dict[str, Any]
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime
    updated_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogRead]
    page: int
    page_size: int
    total: int


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID | None = None
    user_id: UUID | None = None
    notification_type: str
    title: str
    message: str
    status: NotificationStatus
    read_at: datetime | None = None
    payload: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationRead]
    total: int


class CompanyAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str | None = None
    status: SubscriptionStatus
    plan_name: str
    billing_disabled: bool
    ai_requests_monthly: int
    storage_usage_bytes: int
    setup_fee_paid: bool
    trial_end: datetime | None = None
    subscription_end: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CompanyPlanChangeRequest(BaseModel):
    plan_slug: str
    status: SubscriptionStatus | None = None
    billing_disabled: bool | None = None
    setup_fee_paid: bool | None = None
    setup_fee_amount: Decimal | None = Field(default=None, ge=0)
    subscription_end: datetime | None = None
    trial_end: datetime | None = None


class CompanyStatusRequest(BaseModel):
    status: SubscriptionStatus


class AdminCompanyListResponse(BaseModel):
    items: list[CompanyAdminRead]
    total: int


class PlanListResponse(BaseModel):
    items: list[SubscriptionPlanRead]
