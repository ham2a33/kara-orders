import { apiClient } from "@/lib/api-client";
import type {
  AuditLogList,
  CompanyAdminList,
  CompanySubscription,
  CompanyUsage,
  NotificationList,
  PlanList,
  SubscriptionOverview,
  SystemSetting,
} from "@/types/platform";

type RangeParams = {
  page?: number;
  pageSize?: number;
  action?: string;
};

function buildQuery(params: RangeParams = {}): string {
  const searchParams = new URLSearchParams();
  if (params.page) {
    searchParams.set("page", String(params.page));
  }
  if (params.pageSize) {
    searchParams.set("page_size", String(params.pageSize));
  }
  if (params.action) {
    searchParams.set("action", params.action);
  }
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export async function getSubscriptionOverview(): Promise<SubscriptionOverview> {
  return apiClient<SubscriptionOverview>("/platform/subscriptions/me");
}

export async function getUsage(): Promise<CompanyUsage> {
  return apiClient<CompanyUsage>("/platform/usage/me");
}

export async function getBilling(): Promise<CompanySubscription> {
  return apiClient<CompanySubscription>("/platform/billing/me");
}

export async function getPlans(): Promise<PlanList> {
  return apiClient<PlanList>("/platform/plans");
}

export async function getAdminCompanies(): Promise<CompanyAdminList> {
  return apiClient<CompanyAdminList>("/platform/admin/companies");
}

export async function changeCompanyPlan(companyId: string, planSlug: string): Promise<CompanySubscription> {
  return apiClient<CompanySubscription>(`/platform/admin/companies/${companyId}/plan`, {
    method: "PATCH",
    body: { plan_slug: planSlug },
  });
}

export async function changeCompanyStatus(companyId: string, status: string): Promise<CompanySubscription> {
  return apiClient<CompanySubscription>(`/platform/admin/companies/${companyId}/status`, {
    method: "PATCH",
    body: { status },
  });
}

export async function setCompanyBillingDisabled(companyId: string, billingDisabled: boolean): Promise<CompanySubscription> {
  return apiClient<CompanySubscription>(`/platform/admin/companies/${companyId}/billing`, {
    method: "PATCH",
    body: { billing_disabled: billingDisabled },
  });
}

export async function getAuditLogs(params: RangeParams = {}): Promise<AuditLogList> {
  return apiClient<AuditLogList>(`/platform/audit${buildQuery(params)}`);
}

export async function getNotifications(): Promise<NotificationList> {
  return apiClient<NotificationList>("/platform/notifications");
}

export async function markNotificationRead(notificationId: string): Promise<unknown> {
  return apiClient(`/platform/notifications/${notificationId}/read`, {
    method: "POST",
  });
}

export async function getSystemSettings(): Promise<SystemSetting> {
  return apiClient<SystemSetting>("/platform/system/settings");
}

export async function updateSystemSettings(payload: Partial<SystemSetting>): Promise<SystemSetting> {
  return apiClient<SystemSetting>("/platform/system/settings", {
    method: "PATCH",
    body: payload,
  });
}
