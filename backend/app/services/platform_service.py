from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.db.models.audit_log import AuditLog
from app.db.models.company import Company
from app.db.models.company_subscription import CompanySubscription
from app.db.models.company_usage import CompanyUsage
from app.db.models.order import Order
from app.db.models.product import Product
from app.db.models.notification import Notification
from app.db.models.subscription_plan import SubscriptionPlan
from app.db.models.system_setting import SystemSetting
from app.db.models.user import User
from app.db.models.user import User
from app.schemas.platform import (
    AdminCompanyListResponse,
    AuditLogListResponse,
    AuditLogRead,
    CompanyAdminRead,
    CompanyPlanChangeRequest,
    CompanyStatusRequest,
    CompanySubscriptionRead,
    CompanyUsageRead,
    NotificationListResponse,
    NotificationRead,
    PlanListResponse,
    PlanLimitsRead,
    SubscriptionOverviewResponse,
    SubscriptionPlanRead,
    SystemSettingRead,
    SystemSettingUpdateRequest,
)


DEFAULT_BUSINESS_LIMITS = {
    "maximum_users": 20,
    "maximum_products": None,
    "maximum_ai_requests": 1000,
    "maximum_storage_bytes": 10 * 1024 * 1024 * 1024,
    "maximum_companies": 1,
    "maximum_orders_per_month": None,
}


def _default_free_limits() -> dict[str, int | None]:
    return {
        "maximum_users": 5,
        "maximum_products": 100,
        "maximum_ai_requests": 25,
        "maximum_storage_bytes": 250 * 1024 * 1024,
        "maximum_companies": 1,
        "maximum_orders_per_month": 100,
    }


def _default_starter_limits() -> dict[str, int | None]:
    return {
        "maximum_users": 10,
        "maximum_products": 1000,
        "maximum_ai_requests": 250,
        "maximum_storage_bytes": 2 * 1024 * 1024 * 1024,
        "maximum_companies": 1,
        "maximum_orders_per_month": 1000,
    }


def _default_enterprise_limits() -> dict[str, int | None]:
    return {
        "maximum_users": None,
        "maximum_products": None,
        "maximum_ai_requests": None,
        "maximum_storage_bytes": None,
        "maximum_companies": None,
        "maximum_orders_per_month": None,
    }


def _to_decimal(value: object) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class LimitCheck:
    key: str
    current: int
    requested: int


class PlatformService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_default_subscription(self, company: Company) -> CompanySubscription:
        subscription = self.session.scalar(
            select(CompanySubscription)
            .where(CompanySubscription.company_id == company.id)
            .options(selectinload(CompanySubscription.plan))
        )
        if subscription is not None:
            self._sync_period(subscription)
            return subscription

        plan = self.get_plan_by_slug("business")
        now = datetime.now(UTC)
        subscription = CompanySubscription(
            company_id=company.id,
            plan_id=plan.id,
            status="trialing",
            trial_end=now + timedelta(days=14),
            subscription_start=now,
            setup_fee_amount=plan.setup_fee_amount,
            period_start=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        )
        usage = CompanyUsage(
            company_id=company.id,
            period_start=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        )
        self.session.add(subscription)
        self.session.add(usage)
        self.session.flush()
        self.session.add(
            Notification(
                company_id=company.id,
                notification_type="welcome",
                title="Welcome to Kara Orders",
                message="Your subscription is ready. Explore your workspace and start creating orders.",
                payload={"plan": plan.slug},
            )
        )
        self.session.commit()
        self.session.refresh(subscription)
        return subscription

    def get_plan_by_slug(self, slug: str) -> SubscriptionPlan:
        plan = self.session.scalar(select(SubscriptionPlan).where(SubscriptionPlan.slug == slug))
        if plan is None:
            raise NotFoundError("Subscription plan not found")
        return plan

    def list_plans(self) -> PlanListResponse:
        plans = list(
            self.session.scalars(
                select(SubscriptionPlan).where(SubscriptionPlan.is_active.is_(True)).order_by(SubscriptionPlan.price_monthly.asc())
            ).all()
        )
        return PlanListResponse(items=[SubscriptionPlanRead.model_validate(plan) for plan in plans])

    def get_subscription_overview(self, company_id: UUID) -> SubscriptionOverviewResponse:
        subscription = self._get_subscription(company_id)
        usage = self._get_usage(company_id)
        return SubscriptionOverviewResponse(
            subscription=self._serialize_subscription(subscription),
            usage=self._serialize_usage(usage),
            limits=self._serialize_limits(subscription.plan.limits),
        )

    def ensure_limit(
        self,
        company_id: UUID,
        key: str,
        requested: int = 1,
        *,
        current: int | None = None,
        message: str | None = None,
    ) -> None:
        subscription = self._get_subscription(company_id)
        self._ensure_subscription_active(subscription)
        limit = subscription.plan.limits.get(key)
        if limit is None:
            return
        current_value = current if current is not None else self._get_current_usage_value(company_id, key)
        if current_value + requested > int(limit):
            self._notify_limit(company_id, key, int(limit))
            raise ValidationAppError(message or f"{self._friendly_limit_name(key)} limit reached")

    def record_ai_usage(
        self,
        company_id: UUID,
        *,
        tokens_used: int | None,
        recognition_time_ms: int,
        estimated_cost: Decimal = Decimal("0"),
        input_bytes: int = 0,
    ) -> None:
        subscription = self._get_subscription(company_id)
        self._ensure_subscription_active(subscription)
        self.ensure_limit(company_id, "maximum_ai_requests", 1, message="AI request limit reached")
        self._sync_period(subscription)
        usage = self._get_usage(company_id)
        usage.monthly_ai_requests += 1
        subscription.ai_requests_monthly = usage.monthly_ai_requests
        if tokens_used is not None:
            usage.monthly_token_usage += tokens_used
            subscription.ai_tokens_monthly = usage.monthly_token_usage
        usage.recognition_count += 1
        subscription.recognition_count_monthly = usage.recognition_count
        usage.estimated_ai_cost += estimated_cost
        subscription.ai_estimated_cost_monthly = usage.estimated_ai_cost
        prev_count = max(usage.recognition_count - 1, 0)
        if prev_count == 0:
            usage.average_recognition_time_ms = _to_decimal(recognition_time_ms)
        else:
            usage.average_recognition_time_ms = _to_decimal(
                ((usage.average_recognition_time_ms * prev_count) + recognition_time_ms) / usage.recognition_count
            )
        subscription.average_recognition_time_ms = usage.average_recognition_time_ms
        usage.storage_usage_bytes += max(input_bytes, 0)
        subscription.storage_usage_bytes = usage.storage_usage_bytes
        self.session.commit()

    def record_storage_usage(self, company_id: UUID, bytes_used: int) -> None:
        subscription = self._get_subscription(company_id)
        self._ensure_subscription_active(subscription)
        usage = self._get_usage(company_id)
        usage.storage_usage_bytes += max(bytes_used, 0)
        subscription.storage_usage_bytes = usage.storage_usage_bytes
        limit = subscription.plan.limits.get("maximum_storage_bytes")
        if limit is not None and usage.storage_usage_bytes > int(limit):
            self._notify_limit(company_id, "maximum_storage_bytes", int(limit))
            raise ValidationAppError("Storage limit reached")
        self.session.commit()

    def can_create_company(self) -> None:
        plan = self.get_plan_by_slug("free")
        limit = plan.limits.get("maximum_companies")
        if limit is None:
            return
        total_companies = self.session.scalar(select(func.count(Company.id)).where(Company.deleted_at.is_(None))) or 0
        if int(total_companies) >= int(limit):
            raise ValidationAppError("Company limit reached")

    def list_companies(self) -> AdminCompanyListResponse:
        rows = self.session.execute(
            select(Company, CompanySubscription)
            .outerjoin(CompanySubscription, CompanySubscription.company_id == Company.id)
            .options(selectinload(Company.subscription).selectinload(CompanySubscription.plan))
            .order_by(Company.created_at.desc())
        ).all()
        items: list[CompanyAdminRead] = []
        for company, subscription in rows:
            if subscription is None:
                subscription = self.get_or_create_default_subscription(company)
            items.append(self._serialize_company_admin(company, subscription))
        return AdminCompanyListResponse(items=items, total=len(items))

    def change_company_plan(self, company_id: UUID, payload: CompanyPlanChangeRequest) -> CompanySubscriptionRead:
        subscription = self._get_subscription(company_id)
        plan = self.get_plan_by_slug(payload.plan_slug)
        subscription.plan_id = plan.id
        if payload.status is not None:
            subscription.status = payload.status
        if payload.billing_disabled is not None:
            subscription.billing_disabled = payload.billing_disabled
        if payload.setup_fee_paid is not None:
            subscription.setup_fee_paid = payload.setup_fee_paid
        if payload.setup_fee_amount is not None:
            subscription.setup_fee_amount = payload.setup_fee_amount
        if payload.subscription_end is not None:
            subscription.subscription_end = payload.subscription_end
        if payload.trial_end is not None:
            subscription.trial_end = payload.trial_end
        self.session.commit()
        self.session.refresh(subscription)
        return self._serialize_subscription(subscription)

    def change_company_status(self, company_id: UUID, status: str) -> CompanySubscriptionRead:
        subscription = self._get_subscription(company_id)
        subscription.status = status
        self.session.commit()
        self.session.refresh(subscription)
        return self._serialize_subscription(subscription)

    def set_billing_disabled(self, company_id: UUID, disabled: bool) -> CompanySubscriptionRead:
        subscription = self._get_subscription(company_id)
        subscription.billing_disabled = disabled
        self.session.commit()
        self.session.refresh(subscription)
        return self._serialize_subscription(subscription)

    def get_notifications(self, company_id: UUID, *, limit: int = 50) -> NotificationListResponse:
        items = list(
            self.session.scalars(
                select(Notification)
                .where(Notification.company_id == company_id)
                .order_by(Notification.created_at.desc())
                .limit(limit)
            ).all()
        )
        return NotificationListResponse(items=[NotificationRead.model_validate(item) for item in items], total=len(items))

    def mark_notification_read(self, company_id: UUID, notification_id: UUID) -> NotificationRead:
        notification = self.session.scalar(
            select(Notification).where(Notification.id == notification_id, Notification.company_id == company_id)
        )
        if notification is None:
            raise NotFoundError("Notification not found")
        notification.status = "read"
        notification.read_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(notification)
        return NotificationRead.model_validate(notification)

    def get_audit_logs(
        self,
        *,
        company_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20,
        action: str | None = None,
    ) -> AuditLogListResponse:
        statement = select(AuditLog).order_by(AuditLog.created_at.desc())
        if company_id is not None:
            statement = statement.where(AuditLog.company_id == company_id)
        if action:
            statement = statement.where(AuditLog.action == action)
        total = int(self.session.scalar(select(func.count()).select_from(statement.subquery())) or 0)
        items = list(
            self.session.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
        )
        return AuditLogListResponse(
            items=[AuditLogRead.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
        )

    def get_system_settings(self) -> SystemSettingRead:
        settings = self._get_system_settings()
        return SystemSettingRead.model_validate(settings)

    def update_system_settings(self, payload: SystemSettingUpdateRequest) -> SystemSettingRead:
        settings = self._get_system_settings()
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(settings, field, value)
        self.session.commit()
        self.session.refresh(settings)
        return SystemSettingRead.model_validate(settings)

    def log_action(
        self,
        *,
        action: str,
        company_id: UUID | None,
        actor_user_id: UUID | None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.session.add(
            AuditLog(
                company_id=company_id,
                actor_user_id=actor_user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                event_metadata=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        self.session.commit()

    def _ensure_subscription_active(self, subscription: CompanySubscription) -> None:
        if subscription.billing_disabled:
            return
        if subscription.status in {"suspended", "canceled", "expired"}:
            raise ForbiddenError("Subscription is not active")
        if subscription.trial_end is not None and subscription.trial_end < datetime.now(UTC):
            subscription.status = "expired"
            self.session.commit()
            raise ForbiddenError("Subscription has expired")

    def _get_subscription(self, company_id: UUID) -> CompanySubscription:
        subscription = self.session.scalar(
            select(CompanySubscription)
            .where(CompanySubscription.company_id == company_id)
            .options(selectinload(CompanySubscription.plan))
        )
        if subscription is None:
            company = self.session.get(Company, company_id)
            if company is None or company.deleted_at is not None:
                raise NotFoundError("Company not found")
            subscription = self.get_or_create_default_subscription(company)
        self._sync_period(subscription)
        return subscription

    def _get_usage(self, company_id: UUID) -> CompanyUsage:
        usage = self.session.scalar(select(CompanyUsage).where(CompanyUsage.company_id == company_id))
        if usage is None:
            company = self.session.get(Company, company_id)
            if company is None or company.deleted_at is not None:
                raise NotFoundError("Company not found")
            self.get_or_create_default_subscription(company)
            usage = self.session.scalar(select(CompanyUsage).where(CompanyUsage.company_id == company_id))
        if usage is None:
            raise NotFoundError("Usage record not found")
        self._sync_period_usage(usage)
        return usage

    def _sync_period(self, subscription: CompanySubscription) -> None:
        now = datetime.now(UTC)
        if subscription.period_start.year == now.year and subscription.period_start.month == now.month:
            return
        subscription.period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        subscription.ai_requests_monthly = 0
        subscription.ai_tokens_monthly = 0
        subscription.ai_estimated_cost_monthly = Decimal("0")
        subscription.recognition_count_monthly = 0
        subscription.average_recognition_time_ms = Decimal("0")
        subscription.storage_usage_bytes = 0
        self.session.flush()
        usage = self.session.scalar(select(CompanyUsage).where(CompanyUsage.company_id == subscription.company_id))
        if usage is not None:
            self._sync_period_usage(usage)

    def _sync_period_usage(self, usage: CompanyUsage) -> None:
        now = datetime.now(UTC)
        if usage.period_start.year == now.year and usage.period_start.month == now.month:
            return
        usage.period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usage.period_end = None
        usage.monthly_ai_requests = 0
        usage.monthly_token_usage = 0
        usage.estimated_ai_cost = Decimal("0")
        usage.recognition_count = 0
        usage.average_recognition_time_ms = Decimal("0")
        usage.storage_usage_bytes = 0

    def _serialize_subscription(self, subscription: CompanySubscription) -> CompanySubscriptionRead:
        return CompanySubscriptionRead.model_validate(subscription)

    def _serialize_usage(self, usage: CompanyUsage) -> CompanyUsageRead:
        return CompanyUsageRead.model_validate(usage)

    def _serialize_limits(self, limits: dict[str, Any]) -> PlanLimitsRead:
        return PlanLimitsRead(
            maximum_users=limits.get("maximum_users"),
            maximum_products=limits.get("maximum_products"),
            maximum_ai_requests=limits.get("maximum_ai_requests"),
            maximum_storage_bytes=limits.get("maximum_storage_bytes"),
            maximum_companies=limits.get("maximum_companies"),
            maximum_orders_per_month=limits.get("maximum_orders_per_month"),
        )

    def _serialize_company_admin(self, company: Company, subscription: CompanySubscription) -> CompanyAdminRead:
        return CompanyAdminRead(
            id=company.id,
            name=company.name,
            email=company.email,
            status=subscription.status,
            plan_name=subscription.plan.name,
            billing_disabled=subscription.billing_disabled,
            ai_requests_monthly=subscription.ai_requests_monthly,
            storage_usage_bytes=subscription.storage_usage_bytes,
            setup_fee_paid=subscription.setup_fee_paid,
            trial_end=subscription.trial_end,
            subscription_end=subscription.subscription_end,
            created_at=company.created_at,
            updated_at=company.updated_at,
        )

    def _get_current_usage_value(self, company_id: UUID, key: str) -> int:
        usage = self._get_usage(company_id)
        now = datetime.now(UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        mapping = {
            "maximum_ai_requests": usage.monthly_ai_requests,
            "maximum_storage_bytes": usage.storage_usage_bytes,
            "maximum_orders_per_month": int(
                self.session.scalar(
                    select(func.count(Order.id)).where(
                        Order.company_id == company_id,
                        Order.deleted_at.is_(None),
                        Order.created_at >= month_start,
                    )
                )
                or 0
            ),
            "maximum_products": int(
                self.session.scalar(
                    select(func.count(Product.id)).where(
                        Product.company_id == company_id,
                        Product.deleted_at.is_(None),
                    )
                )
                or 0
            ),
            "maximum_users": int(
                self.session.scalar(
                    select(func.count(User.id)).where(
                        User.company_id == company_id,
                        User.deleted_at.is_(None),
                        User.is_active.is_(True),
                    )
                )
                or 0
            ),
        }
        return int(mapping.get(key, 0) or 0)

    def _notify_limit(self, company_id: UUID, key: str, limit: int) -> None:
        title = {
            "maximum_ai_requests": "AI limit reached",
            "maximum_storage_bytes": "Storage limit reached",
            "maximum_orders_per_month": "Order limit reached",
            "maximum_products": "Product limit reached",
            "maximum_users": "User limit reached",
        }.get(key, "Plan limit reached")
        self.session.add(
            Notification(
                company_id=company_id,
                notification_type="limit_reached",
                title=title,
                message=f"Your current plan limit for {key} has reached {limit}.",
                payload={"key": key, "limit": limit},
            )
        )
        self.session.commit()

    def _friendly_limit_name(self, key: str) -> str:
        return {
            "maximum_ai_requests": "AI request",
            "maximum_storage_bytes": "Storage",
            "maximum_orders_per_month": "Order",
            "maximum_products": "Product",
            "maximum_users": "User",
        }.get(key, key)

    def _get_system_settings(self) -> SystemSetting:
        settings = self.session.scalar(select(SystemSetting))
        if settings is None:
            settings = SystemSetting()
            self.session.add(settings)
            self.session.commit()
            self.session.refresh(settings)
        return settings
