import type { Company } from "@/types/company";

export interface SessionUser {
  id: string;
  company_id: string;
  email: string;
  full_name: string | null;
  role: "owner" | "admin" | "manager" | "employee";
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MeResponse {
  user: SessionUser;
  company: Company;
}
