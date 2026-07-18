import { apiClient, apiDownload } from "@/lib/api-client";
import type {
  AnalyticsFormat,
  AnalyticsPreset,
  CustomersAnalyticsResponse,
  DashboardResponse,
  OrdersAnalyticsResponse,
  ProductsAnalyticsResponse,
  RevenueAnalyticsResponse,
} from "@/types/analytics";

type RangeParams = {
  preset?: AnalyticsPreset;
  startDate?: string;
  endDate?: string;
};

function buildQuery(params: RangeParams = {}): string {
  const searchParams = new URLSearchParams();
  if (params.preset) {
    searchParams.set("preset", params.preset);
  }
  if (params.startDate) {
    searchParams.set("start_date", params.startDate);
  }
  if (params.endDate) {
    searchParams.set("end_date", params.endDate);
  }
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export function buildAnalyticsExportUrl(
  format: AnalyticsFormat,
  params: RangeParams = {},
): string {
  const searchParams = new URLSearchParams();
  searchParams.set("format", format);
  if (params.preset) {
    searchParams.set("preset", params.preset);
  }
  if (params.startDate) {
    searchParams.set("start_date", params.startDate);
  }
  if (params.endDate) {
    searchParams.set("end_date", params.endDate);
  }
  const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
  const path = `/analytics/export?${searchParams.toString()}`;
  return baseUrl ? new URL(path, baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`).toString() : path;
}

export async function downloadAnalyticsExport(format: AnalyticsFormat, params: RangeParams = {}): Promise<void> {
  const searchParams = new URLSearchParams();
  searchParams.set("format", format);
  if (params.preset) {
    searchParams.set("preset", params.preset);
  }
  if (params.startDate) {
    searchParams.set("start_date", params.startDate);
  }
  if (params.endDate) {
    searchParams.set("end_date", params.endDate);
  }
  await apiDownload(`/analytics/export?${searchParams.toString()}`, `analytics-${format}`);
}

export async function getDashboardAnalytics(params: RangeParams = {}): Promise<DashboardResponse> {
  return apiClient<DashboardResponse>(`/dashboard${buildQuery(params)}`);
}

export async function getRevenueAnalytics(params: RangeParams = {}): Promise<RevenueAnalyticsResponse> {
  return apiClient<RevenueAnalyticsResponse>(`/analytics/revenue${buildQuery(params)}`);
}

export async function getOrdersAnalytics(params: RangeParams = {}): Promise<OrdersAnalyticsResponse> {
  return apiClient<OrdersAnalyticsResponse>(`/analytics/orders${buildQuery(params)}`);
}

export async function getProductsAnalytics(params: RangeParams = {}): Promise<ProductsAnalyticsResponse> {
  return apiClient<ProductsAnalyticsResponse>(`/analytics/products${buildQuery(params)}`);
}

export async function getCustomersAnalytics(params: RangeParams = {}): Promise<CustomersAnalyticsResponse> {
  return apiClient<CustomersAnalyticsResponse>(`/analytics/customers${buildQuery(params)}`);
}
