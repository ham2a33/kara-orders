import { apiClient } from "@/lib/api-client";
import type { MeResponse } from "@/types/session";

export function getCurrentSession(): Promise<MeResponse> {
  return apiClient<MeResponse>("/auth/me");
}
