import { apiClient } from "@/lib/api-client";
import type { InvoicePreview, Order, OrderCreatePayload, OrderListResponse, OrderStatus, OrderUpdatePayload } from "@/types/orders";

type OrderQuery = {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: OrderStatus;
  includeDeleted?: boolean;
  sortBy?: string;
  sortDir?: "asc" | "desc";
};

function buildQuery(params: OrderQuery = {}): string {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set("page", String(params.page));
  if (params.pageSize) searchParams.set("page_size", String(params.pageSize));
  if (params.search) searchParams.set("search", params.search);
  if (params.status) searchParams.set("status", params.status);
  if (params.includeDeleted) searchParams.set("include_deleted", "true");
  if (params.sortBy) searchParams.set("sort_by", params.sortBy);
  if (params.sortDir) searchParams.set("sort_dir", params.sortDir);
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export async function getOrders(params: OrderQuery = {}): Promise<OrderListResponse> {
  return apiClient<OrderListResponse>(`/orders${buildQuery(params)}`);
}

export async function getOrder(orderId: string): Promise<Order> {
  return apiClient<Order>(`/orders/${orderId}`);
}

export async function createOrder(payload: OrderCreatePayload): Promise<Order> {
  return apiClient<Order>("/orders", { method: "POST", body: payload });
}

export async function updateOrder(orderId: string, payload: OrderUpdatePayload): Promise<Order> {
  return apiClient<Order>(`/orders/${orderId}`, { method: "PATCH", body: payload });
}

export async function deleteOrder(orderId: string): Promise<{ detail: string }> {
  return apiClient(`/orders/${orderId}`, { method: "DELETE" });
}

export async function restoreOrder(orderId: string): Promise<{ detail: string }> {
  return apiClient(`/orders/${orderId}/restore`, { method: "POST" });
}

export async function getInvoicePreview(orderId: string): Promise<InvoicePreview> {
  return apiClient<InvoicePreview>(`/orders/${orderId}/invoice/preview`);
}
