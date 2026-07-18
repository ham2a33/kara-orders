export type AnalyticsPreset =
  | "today"
  | "yesterday"
  | "last_7_days"
  | "last_30_days"
  | "this_month"
  | "last_month";

export type AnalyticsFormat = "csv" | "excel" | "pdf";

export type AnalyticsRange = {
  preset: AnalyticsPreset;
  start_date: string;
  end_date: string;
  timezone: string;
};

export type AnalyticsSeriesPoint = {
  label: string;
  value: string;
  count: number;
};

export type DashboardMetrics = {
  today_revenue: string;
  week_revenue: string;
  month_revenue: string;
  today_orders: number;
  week_orders: number;
  month_orders: number;
  average_invoice: string;
  total_products: number;
  low_stock_products: number;
  out_of_stock_products: number;
};

export type AnalyticsStatusBreakdown = {
  draft_orders: number;
  confirmed_orders: number;
  completed_orders: number;
  cancelled_orders: number;
  average_order_value: string;
  largest_order: string;
};

export type InventorySummary = {
  total_products: number;
  low_stock_products: number;
  out_of_stock_products: number;
  inventory_value: string;
};

export type TopProduct = {
  product_id: string | null;
  product_name: string;
  sku: string | null;
  unit: string | null;
  quantity_sold: string;
  revenue: string;
  order_count: number;
};

export type TopCategory = {
  category_name: string;
  quantity_sold: string;
  revenue: string;
  product_count: number;
};

export type TopCustomer = {
  customer_name: string;
  customer_phone: string | null;
  order_count: number;
  revenue: string;
  last_order_at: string;
};

export type RecentOrder = {
  id: string;
  invoice_number: string;
  customer_name: string | null;
  customer_phone: string | null;
  status: string;
  total: string;
  created_at: string;
};

export type DashboardResponse = {
  range: AnalyticsRange;
  metrics: DashboardMetrics;
  revenue_by_day: AnalyticsSeriesPoint[];
  orders_by_day: AnalyticsSeriesPoint[];
  top_products: TopProduct[];
  top_categories: TopCategory[];
  top_customers: TopCustomer[];
  recent_orders: RecentOrder[];
  inventory_summary: InventorySummary;
};

export type RevenueAnalyticsResponse = {
  range: AnalyticsRange;
  daily: AnalyticsSeriesPoint[];
  monthly: AnalyticsSeriesPoint[];
  metrics: DashboardMetrics;
};

export type OrdersAnalyticsResponse = {
  range: AnalyticsRange;
  daily: AnalyticsSeriesPoint[];
  monthly: AnalyticsSeriesPoint[];
  status_breakdown: AnalyticsStatusBreakdown;
  recent_orders: RecentOrder[];
};

export type ProductsAnalyticsResponse = {
  range: AnalyticsRange;
  top_products: TopProduct[];
  top_categories: TopCategory[];
  inventory_summary: InventorySummary;
};

export type CustomersAnalyticsResponse = {
  range: AnalyticsRange;
  top_customers: TopCustomer[];
  recent_orders: RecentOrder[];
};

