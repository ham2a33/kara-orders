import { apiClient } from "@/lib/api-client";
import type {
  Product,
  ProductCategory,
  ProductCategoryPayload,
  ProductCreatePayload,
  ProductInventory,
  ProductInventoryTransaction,
  ProductListResponse,
  ProductUpdatePayload,
} from "@/types/products";

type ProductQuery = {
  page?: number;
  pageSize?: number;
  search?: string;
  categoryId?: string;
  tagId?: string;
  isActive?: boolean;
  includeDeleted?: boolean;
  sortBy?: string;
  sortDir?: "asc" | "desc";
};

function buildQuery(params: ProductQuery = {}): string {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set("page", String(params.page));
  if (params.pageSize) searchParams.set("page_size", String(params.pageSize));
  if (params.search) searchParams.set("search", params.search);
  if (params.categoryId) searchParams.set("category_id", params.categoryId);
  if (params.tagId) searchParams.set("tag_id", params.tagId);
  if (params.isActive !== undefined) searchParams.set("is_active", String(params.isActive));
  if (params.includeDeleted) searchParams.set("include_deleted", "true");
  if (params.sortBy) searchParams.set("sort_by", params.sortBy);
  if (params.sortDir) searchParams.set("sort_dir", params.sortDir);
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export async function getProducts(params: ProductQuery = {}): Promise<ProductListResponse> {
  return apiClient<ProductListResponse>(`/products${buildQuery(params)}`);
}

export async function getProduct(productId: string): Promise<Product> {
  return apiClient<Product>(`/products/${productId}`);
}

export async function createProduct(payload: ProductCreatePayload): Promise<Product> {
  return apiClient<Product>("/products", { method: "POST", body: payload });
}

export async function updateProduct(productId: string, payload: ProductUpdatePayload): Promise<Product> {
  return apiClient<Product>(`/products/${productId}`, { method: "PATCH", body: payload });
}

export async function deleteProduct(productId: string): Promise<{ detail: string }> {
  return apiClient(`/products/${productId}`, { method: "DELETE" });
}

export async function restoreProduct(productId: string): Promise<{ detail: string }> {
  return apiClient(`/products/${productId}/restore`, { method: "POST" });
}

export async function getCategories(): Promise<{ items: ProductCategory[] }> {
  return apiClient<{ items: ProductCategory[] }>("/products/categories");
}

export async function createCategory(payload: ProductCategoryPayload): Promise<ProductCategory> {
  return apiClient<ProductCategory>("/products/categories", { method: "POST", body: payload });
}

export async function getInventory(productId: string): Promise<ProductInventory> {
  return apiClient<ProductInventory>(`/products/${productId}/inventory`);
}

export async function getInventoryHistory(productId: string): Promise<ProductInventoryTransaction[]> {
  return apiClient<ProductInventoryTransaction[]>(`/products/${productId}/inventory/history`);
}
