import type { Product } from "@/types/products";

function normalizeText(value: string): string {
  return value.trim().toLowerCase().replace(/ё/g, "е");
}

export function rankProductForSearch(product: Product, searchValue: string): number {
  const query = normalizeText(searchValue);
  if (!query) {
    return 0;
  }

  const name = normalizeText(product.name);
  const sku = normalizeText(product.sku ?? "");
  const barcode = normalizeText(product.barcode ?? "");
  const manufacturer = normalizeText(product.manufacturer ?? "");
  const aliases = normalizeText(product.aliases.join(" "));
  const category = normalizeText(product.category ?? "");

  if (name === query) {
    return 1000;
  }
  if (sku === query || barcode === query) {
    return 950;
  }
  if (name.startsWith(query)) {
    return 900;
  }
  if (sku.startsWith(query) || barcode.startsWith(query)) {
    return 850;
  }
  if (name.includes(query)) {
    return 800;
  }
  if (aliases.includes(query)) {
    return 750;
  }
  if (manufacturer.includes(query)) {
    return 700;
  }
  if (sku.includes(query) || barcode.includes(query)) {
    return 650;
  }
  if (category.includes(query)) {
    return 600;
  }

  const blob = [name, sku, barcode, manufacturer, aliases, category].join(" ");
  return blob.includes(query) ? 500 : 0;
}

export function sortProductsBySearch(products: Product[], searchValue: string): Product[] {
  return [...products].sort(
    (left, right) => rankProductForSearch(right, searchValue) - rankProductForSearch(left, searchValue),
  );
}
