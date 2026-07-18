from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.dependencies.auth import get_current_user, require_super_admin
from app.dependencies.deps import get_db
from app.db.models.user import User
from app.schemas.platform import (
    AdminCompanyListResponse,
    AuditLogListResponse,
    CompanyPlanChangeRequest,
    CompanyStatusRequest,
    CompanySubscriptionRead,
    CompanyUsageRead,
    NotificationListResponse,
    NotificationRead,
    PlanListResponse,
    SubscriptionOverviewResponse,
    SystemSettingRead,
    SystemSettingUpdateRequest,
)
from app.services.platform_service import PlatformService

router = APIRouter(prefix="/platform", tags=["platform"])


def _service(session: Session) -> PlatformService:
    return PlatformService(session)


@router.get("/subscriptions/me", response_model=SubscriptionOverviewResponse)
def get_my_subscription(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> SubscriptionOverviewResponse:
    return _service(session).get_subscription_overview(current_user.company_id)


@router.get("/usage/me", response_model=CompanyUsageRead)
def get_my_usage(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CompanyUsageRead:
    return _service(session).get_subscription_overview(current_user.company_id).usage


@router.get("/billing/me", response_model=CompanySubscriptionRead)
def get_my_billing(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CompanySubscriptionRead:
    return _service(session).get_subscription_overview(current_user.company_id).subscription


@router.get("/plans", response_model=PlanListResponse, dependencies=[Depends(require_super_admin)])
def list_plans(
    session: Session = Depends(get_db),
) -> PlanListResponse:
    return _service(session).list_plans()


@router.get("/admin/companies", response_model=AdminCompanyListResponse, dependencies=[Depends(require_super_admin)])
def list_admin_companies(session: Session = Depends(get_db)) -> AdminCompanyListResponse:
    return _service(session).list_companies()


@router.patch("/admin/companies/{company_id}/plan", response_model=CompanySubscriptionRead, dependencies=[Depends(require_super_admin)])
def change_company_plan(
    company_id: UUID,
    payload: CompanyPlanChangeRequest,
    session: Session = Depends(get_db),
) -> CompanySubscriptionRead:
    return _service(session).change_company_plan(company_id, payload)


@router.patch("/admin/companies/{company_id}/status", response_model=CompanySubscriptionRead, dependencies=[Depends(require_super_admin)])
def change_company_status(
    company_id: UUID,
    payload: CompanyStatusRequest,
    session: Session = Depends(get_db),
) -> CompanySubscriptionRead:
    return _service(session).change_company_status(company_id, payload.status)


@router.patch("/admin/companies/{company_id}/billing", response_model=CompanySubscriptionRead, dependencies=[Depends(require_super_admin)])
def set_company_billing(
    company_id: UUID,
    payload: dict[str, bool],
    session: Session = Depends(get_db),
) -> CompanySubscriptionRead:
    return _service(session).set_billing_disabled(company_id, bool(payload.get("billing_disabled", False)))


@router.get("/audit", response_model=AuditLogListResponse)
def list_audit_logs(
    page: int = 1,
    page_size: int = 20,
    action: str | None = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> AuditLogListResponse:
    if current_user.is_super_admin:
        return _service(session).get_audit_logs(page=page, page_size=page_size, action=action)
    return _service(session).get_audit_logs(company_id=current_user.company_id, page=page, page_size=page_size, action=action)


@router.get("/notifications", response_model=NotificationListResponse)
def list_notifications(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> NotificationListResponse:
    return _service(session).get_notifications(current_user.company_id)


@router.post("/notifications/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> NotificationRead:
    return _service(session).mark_notification_read(current_user.company_id, notification_id)


@router.get("/system/settings", response_model=SystemSettingRead, dependencies=[Depends(require_super_admin)])
def get_system_settings(session: Session = Depends(get_db)) -> SystemSettingRead:
    return _service(session).get_system_settings()


@router.patch("/system/settings", response_model=SystemSettingRead, dependencies=[Depends(require_super_admin)])
def update_system_settings(
    payload: SystemSettingUpdateRequest,
    session: Session = Depends(get_db),
) -> SystemSettingRead:
    return _service(session).update_system_settings(payload)
