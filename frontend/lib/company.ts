import { apiClient } from "@/lib/api-client";
import type {
  Company,
  CompanyInvitationCreateResponse,
  CompanyInvitationsResponse,
  CompanyInvitePayload,
  CompanyLogoResponse,
  CompanyUpdatePayload,
  CompanyUsersResponse,
  CompanyRole,
} from "@/types/company";

export async function getMyCompany(): Promise<Company> {
  return apiClient<Company>("/companies/me");
}

export async function updateMyCompany(payload: CompanyUpdatePayload): Promise<Company> {
  return apiClient<Company>("/companies/me", {
    method: "PATCH",
    body: payload,
  });
}

export async function uploadCompanyLogo(file: File): Promise<CompanyLogoResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient<CompanyLogoResponse>("/companies/me/logo", {
    method: "POST",
    body: formData,
  });
}

export async function uploadInvoiceLogo(file: File): Promise<CompanyLogoResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient<CompanyLogoResponse>("/companies/me/invoice-logo", {
    method: "POST",
    body: formData,
  });
}

export async function getCompanyUsers(): Promise<CompanyUsersResponse> {
  return apiClient<CompanyUsersResponse>("/companies/me/users");
}

export async function getCompanyInvitations(): Promise<CompanyInvitationsResponse> {
  return apiClient<CompanyInvitationsResponse>("/companies/me/users/invitations");
}

export async function inviteCompanyUser(payload: CompanyInvitePayload): Promise<CompanyInvitationCreateResponse> {
  return apiClient<CompanyInvitationCreateResponse>("/companies/me/users/invitations", {
    method: "POST",
    body: payload,
  });
}

export async function changeCompanyUserRole(userId: string, role: CompanyRole): Promise<unknown> {
  return apiClient(`/companies/me/users/${userId}/role`, {
    method: "PATCH",
    body: { role },
  });
}

export async function removeCompanyUser(userId: string): Promise<unknown> {
  return apiClient(`/companies/me/users/${userId}`, {
    method: "DELETE",
  });
}
