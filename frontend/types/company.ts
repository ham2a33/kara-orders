export type CompanyRole = "owner" | "admin" | "manager" | "employee";

export type Company = {
  id: string;
  name: string;
  logo_url: string | null;
  invoice_logo_url: string | null;
  email: string | null;
  website: string | null;
  timezone: string;
  language: string;
  bin_tax_id: string | null;
  currency: string;
  invoice_prefix: string;
  invoice_number_format: string;
  next_invoice_number: number;
  tax_percentage: string;
  footer_text: string | null;
  payment_information: string | null;
  notes: string | null;
  address: string | null;
  phone: string | null;
  created_at: string;
  updated_at: string;
};

export type CompanyUpdatePayload = Partial<{
  name: string;
  email: string | null;
  website: string | null;
  timezone: string | null;
  language: string | null;
  bin_tax_id: string | null;
  currency: string | null;
  address: string | null;
  phone: string | null;
  logo_url: string | null;
  invoice_logo_url: string | null;
  invoice_prefix: string | null;
  invoice_number_format: string | null;
  tax_percentage: string | number | null;
  footer_text: string | null;
  payment_information: string | null;
  notes: string | null;
}>;

export type CompanyUser = {
  id: string;
  company_id: string;
  email: string;
  full_name: string | null;
  role: CompanyRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
};

export type CompanyUsersResponse = {
  items: CompanyUser[];
};

export type CompanyInvitation = {
  id: string;
  company_id: string;
  email: string;
  full_name: string | null;
  role: CompanyRole;
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CompanyInvitationsResponse = {
  items: CompanyInvitation[];
};

export type CompanyInvitationCreateResponse = {
  invitation: CompanyInvitation;
  invite_token: string;
};

export type CompanyInvitePayload = {
  email: string;
  full_name?: string | null;
  role: Exclude<CompanyRole, "owner">;
};

export type CompanyLogoResponse = {
  url: string;
};
