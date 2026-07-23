export type OrderStatus = "new" | "confirmed" | "deleted";

export type OrderItem = {
  id: string;
  order_id: string;
  product_id: string | null;
  product_name: string;
  quantity: string;
  unit_price: string;
  discount_amount: string;
  tax_amount: string;
  line_total: string;
  ai_confidence: string | null;
  product: unknown | null;
};

export type Order = {
  id: string;
  company_id: string;
  invoice_number: string;
  customer_name: string | null;
  customer_phone: string | null;
  customer_address: string | null;
  notes: string | null;
  input_method: string;
  status: OrderStatus;
  subtotal: string;
  discount_total: string;
  tax_total: string;
  total: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  items: OrderItem[];
};

export type OrderListResponse = {
  items: Order[];
  page: number;
  page_size: number;
  total: number;
};

export type OrderCreatePayload = {
  customer_name?: string | null;
  customer_phone?: string | null;
  customer_address?: string | null;
  notes?: string | null;
  status?: OrderStatus;
  items: Array<{
    product_id: string;
    quantity: string | number;
    discount_amount?: string | number | null;
  }>;
};

export type OrderUpdatePayload = Partial<OrderCreatePayload>;

export type InvoicePreview = {
  order: Order;
  company_name: string;
  pdf_url: string | null;
};
