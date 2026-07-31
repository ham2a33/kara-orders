import type { AIRecognition, AIRecognitionItem } from "@/types/ai";
import type { Product } from "@/types/products";
import { buildProductDisplayName } from "@/lib/product-size";
import { resolveOrderUnit, type OrderUnitValue } from "@/lib/order-units";

export type EditableOrderLine = {
  key: string;
  product: Product | null;
  pendingLabel: string | null;
  pendingSize: string | null;
  quantity: number;
  unit: OrderUnitValue;
  unitPrice: number;
  discountAmount: number;
  /** Index of the source recognition item, so a manual pick can be sent back for learning. */
  aiItemIndex: number | null;
  candidates: Product[];
};

function candidateToProduct(
  candidate: AIRecognitionItem["candidate_products"][number],
): Product {
  return {
    id: candidate.id,
    company_id: "",
    category_id: null,
    name: candidate.name,
    description: null,
    size: null,
    manufacturer: candidate.manufacturer,
    sku: candidate.sku,
    barcode: null,
    aliases: [],
    category: null,
    unit: "pcs",
    currency: "KZT",
    price: candidate.price,
    cost: null,
    tax_rate: null,
    stock_qty: candidate.stock_quantity,
    low_stock_threshold: null,
    is_active: true,
    created_at: "",
    updated_at: "",
    deleted_at: null,
    stock_value: "0",
    low_stock: false,
    tags: [],
    images: candidate.image_url
      ? [
          {
            id: candidate.id,
            product_id: candidate.id,
            url: candidate.image_url,
            storage_path: null,
            alt_text: null,
            sort_order: 0,
            is_primary: true,
            created_at: "",
            updated_at: "",
          },
        ]
      : [],
    category_rel: null,
  };
}

export function resolveAiItemProduct(item: AIRecognitionItem): Product | null {
  if (item.matched_product) {
    return item.matched_product as Product;
  }
  if (item.selected_product_id) {
    const candidate = item.candidate_products.find(
      (entry) => entry.id === item.selected_product_id,
    );
    if (candidate) {
      return candidateToProduct(candidate);
    }
  }
  if (item.candidate_products.length === 1) {
    return candidateToProduct(item.candidate_products[0]);
  }
  return null;
}

export function formatLineSize(
  product: Product | null,
  pendingSize: string | null,
): string {
  const fromProduct = product?.size?.trim();
  if (fromProduct) {
    return fromProduct;
  }
  return pendingSize?.trim() || "—";
}

export function buildEditableLinesFromRecognition(
  recognition: AIRecognition,
): EditableOrderLine[] {
  return recognition.items.map((item, index) => {
    const product = resolveAiItemProduct(item);
    const unit = product
      ? resolveOrderUnit(product)
      : resolveOrderUnit({ unit: item.unit ?? "pcs" } as Product);
    const unitPrice = product ? Number(product.price || 0) : 0;
    const quantity = Number(item.quantity);
    return {
      key: `ai-${recognition.id}-${index}`,
      product,
      pendingLabel: product ? null : item.recognized_name || item.product_name,
      pendingSize: item.size,
      quantity: Number.isFinite(quantity) && quantity > 0 ? quantity : 1,
      unit,
      unitPrice,
      discountAmount: 0,
      aiItemIndex: index,
      candidates: item.candidate_products.map(candidateToProduct),
    };
  });
}

export function buildManualLine(
  product: Product,
  key: string,
): EditableOrderLine {
  return {
    key,
    product,
    pendingLabel: null,
    pendingSize: null,
    quantity: 1,
    unit: resolveOrderUnit(product),
    unitPrice: Number(product.price || 0),
    discountAmount: 0,
    aiItemIndex: null,
    candidates: [],
  };
}

export function attachProductToLine(
  line: EditableOrderLine,
  product: Product,
): EditableOrderLine {
  return {
    ...line,
    product,
    pendingLabel: null,
    unit: resolveOrderUnit(product),
    unitPrice: Number(product.price || 0),
  };
}

export function productSearchLabel(product: Product): string {
  const size = product.size?.trim();
  if (size) {
    return buildProductDisplayName(product.name, size);
  }
  return product.name;
}
