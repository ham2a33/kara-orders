export type ProductTag = {
  id: string;
  name: string;
  slug: string;
  color: string | null;
  is_active: boolean;
};

export type ProductCategory = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  parent_id: string | null;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  product_count: number;
  children: ProductCategory[];
};

export type Product = {
  id: string;
  company_id: string;
  category_id: string | null;
  name: string;
  sku: string | null;
  barcode: string | null;
  aliases: string[];
  category: string | null;
  unit: string;
  currency: string;
  price: string;
  cost: string | null;
  tax_rate: string | null;
  stock_qty: string | null;
  low_stock_threshold: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  stock_value: string;
  low_stock: boolean;
  tags: ProductTag[];
  images: Array<{
    id: string;
    product_id: string;
    url: string;
    storage_path: string | null;
    alt_text: string | null;
    sort_order: number;
    is_primary: boolean;
    created_at: string;
    updated_at: string;
  }>;
  category_rel: ProductCategory | null;
};

export type ProductListResponse = {
  items: Product[];
  page: number;
  page_size: number;
  total: number;
};

export type ProductInventory = {
  current_stock: string;
  stock_value: string;
  low_stock: boolean;
};

export type ProductInventoryTransaction = {
  id: string;
  product_id: string;
  transaction_type: string;
  quantity: string;
  quantity_before: string;
  quantity_after: string;
  unit_cost: string | null;
  note: string | null;
  created_by_id: string;
  created_at: string;
  updated_at: string;
};

export type ProductCreatePayload = {
  name: string;
  sku?: string | null;
  barcode?: string | null;
  aliases?: string[];
  category?: string | null;
  unit?: string;
  currency?: string;
  price: string | number;
  cost?: string | number | null;
  tax_rate?: string | number | null;
  stock_qty?: string | number | null;
  low_stock_threshold?: string | number | null;
  is_active?: boolean;
};

export type ProductUpdatePayload = Partial<ProductCreatePayload>;

export type ProductCategoryPayload = {
  name: string;
  slug: string;
  description?: string | null;
  parent_id?: string | null;
  sort_order?: number;
  is_active?: boolean;
};
