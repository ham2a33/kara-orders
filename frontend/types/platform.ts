export type SubscriptionStatus =
  | "trialing"
  | "active"
  | "past_due"
  | "suspended"
  | "expired"
  | "canceled"
  | "lifetime"
  | "custom";

export type NotificationStatus = "unread" | "read" | "archived";

export type PlanLimits = {
  maximum_users: number | null;
  maximum_products: number | null;
  maximum_ai_requests: number | null;
  maximum_storage_bytes: number | null;
  maximum_companies: number | null;
  maximum_orders_per_month: number | null;
};

export type SubscriptionPlan = {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  currency: string;
  price_monthly: string;
  setup_fee_amount: string;
  billing_cycle: string;
  is_default: boolean;
  is_active: boolean;
  features: Record<string, unknown>;
  limits: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type CompanySubscription = {
  id: string;
  company_id: string;
  plan: SubscriptionPlan;
  status: SubscriptionStatus;
  trial_end: string | null;
  subscription_start: string | null;
  subscription_end: string | null;
  billing_disabled: boolean;
  setup_fee_paid: boolean;
  setup_fee_amount: string;
  setup_fee_paid_at: string | null;
  period_start: string;
  ai_requests_monthly: number;
  ai_tokens_monthly: number;
  ai_estimated_cost_monthly: string;
  recognition_count_monthly: number;
  average_recognition_time_ms: string;
  storage_usage_bytes: number;
  extra: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type CompanyUsage = {
  id: string;
  company_id: string;
  period_start: string;
  period_end: string | null;
  monthly_ai_requests: number;
  monthly_token_usage: number;
  estimated_ai_cost: string;
  recognition_count: number;
  average_recognition_time_ms: string;
  storage_usage_bytes: number;
  created_at: string;
  updated_at: string;
};

export type SubscriptionOverview = {
  subscription: CompanySubscription;
  usage: CompanyUsage;
  limits: PlanLimits;
};

export type SystemSetting = {
  id: string;
  ai_enabled: boolean;
  maintenance_mode: boolean;
  max_upload_size_mb: number;
  allowed_file_types: string[];
  default_currency: string;
  default_tax: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type AuditLog = {
  id: string;
  company_id: string | null;
  actor_user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  description: string | null;
  event_metadata: Record<string, unknown>;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  updated_at: string;
};

export type AuditLogList = {
  items: AuditLog[];
  page: number;
  page_size: number;
  total: number;
};

export type Notification = {
  id: string;
  company_id: string | null;
  user_id: string | null;
  notification_type: string;
  title: string;
  message: string;
  status: NotificationStatus;
  read_at: string | null;
  payload: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type NotificationList = {
  items: Notification[];
  total: number;
};

export type CompanyAdmin = {
  id: string;
  name: string;
  email: string | null;
  status: SubscriptionStatus;
  plan_name: string;
  billing_disabled: boolean;
  ai_requests_monthly: number;
  storage_usage_bytes: number;
  setup_fee_paid: boolean;
  trial_end: string | null;
  subscription_end: string | null;
  created_at: string;
  updated_at: string;
};

export type CompanyAdminList = {
  items: CompanyAdmin[];
  total: number;
};

export type PlanList = {
  items: SubscriptionPlan[];
};
