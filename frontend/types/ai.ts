export type AIInputType = "photo" | "voice" | "text" | "pdf";
export type AIRecognitionStatus = "completed" | "needs_review" | "failed" | "converted";
export type AIItemStatus = "matched" | "needs_review" | "unmatched";

export type AIRecognitionItem = {
  product_name: string;
  quantity: string;
  unit: string | null;
  confidence: string;
  status: AIItemStatus;
  match_method: string | null;
  needs_review: boolean;
  matched_product: {
    id: string;
    name: string;
    sku: string | null;
    barcode: string | null;
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
    tags: Array<{
      id: string;
      name: string;
      slug: string;
      color: string | null;
      is_active: boolean;
    }>;
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
    category_rel: unknown | null;
  } | null;
};

export type AIRecognition = {
  id: string;
  company_id: string;
  user_id: string;
  input_type: AIInputType;
  status: AIRecognitionStatus;
  model_used: string;
  confidence: string | null;
  tokens_used: number | null;
  recognition_time_ms: number | null;
  original_text: string | null;
  original_file_url: string | null;
  original_file_path: string | null;
  original_file_name: string | null;
  original_file_mime_type: string | null;
  raw_ai_response: Record<string, unknown> | null;
  recognized_payload: Record<string, unknown> | null;
  matched_payload: Record<string, unknown> | null;
  error_message: string | null;
  created_order_id: string | null;
  created_at: string;
  updated_at: string;
  items: AIRecognitionItem[];
};

export type AIRecognitionListResponse = {
  items: AIRecognition[];
  page: number;
  page_size: number;
  total: number;
};

export type AIRecognitionConfirmPayload = {
  customer_name?: string | null;
  customer_phone?: string | null;
  customer_address?: string | null;
  notes?: string | null;
  status?: "draft" | "confirmed" | "completed" | "cancelled";
  items: Array<{
    product_id: string;
    quantity: string | number;
    discount_amount?: string | number | null;
  }>;
};

export type AIRecognitionConfirmResponse = {
  recognition: AIRecognition;
  order: {
    id: string;
    company_id: string;
    invoice_number: string;
    customer_name: string | null;
    customer_phone: string | null;
    customer_address: string | null;
    notes: string | null;
    input_method: string;
    status: string;
    subtotal: string;
    discount_total: string;
    tax_total: string;
    total: string;
    created_by: string;
    created_at: string;
    updated_at: string;
    deleted_at: string | null;
    items: Array<{
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
    }>;
  };
};
