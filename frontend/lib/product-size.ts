export const PRODUCT_SIZE_UNIT_SUFFIXES = [
  { id: "mm", label: "мм" },
  { id: "cm", label: "см" },
  { id: "m", label: "м" },
  { id: "kg", label: "кг" },
  { id: "g", label: "г" },
  { id: "l", label: "л" },
  { id: "ml", label: "мл" },
  { id: "m2", label: "м²" },
  { id: "m3", label: "м³" },
  { id: "inch", label: "дюйм (\")" },
  { id: "pn", label: "PN" },
  { id: "sdr", label: "SDR" },
  { id: "text", label: "текст" },
] as const;

export type ProductSizeUnitId = (typeof PRODUCT_SIZE_UNIT_SUFFIXES)[number]["id"];

export function formatProductSizeValue(value: string, unit: ProductSizeUnitId): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return "";
  }
  if (unit === "text") {
    return trimmed;
  }
  if (unit === "inch") {
    return trimmed.includes('"') ? trimmed : `${trimmed}"`;
  }
  if (unit === "pn") {
    return trimmed.toUpperCase().startsWith("PN") ? trimmed.toUpperCase() : `PN${trimmed}`;
  }
  if (unit === "sdr") {
    return trimmed.toUpperCase().startsWith("SDR") ? trimmed.toUpperCase() : `SDR${trimmed}`;
  }
  const suffixMap: Record<Exclude<ProductSizeUnitId, "text" | "inch" | "pn" | "sdr">, string> = {
    mm: "мм",
    cm: "см",
    m: "м",
    kg: "кг",
    g: "г",
    l: "л",
    ml: "мл",
    m2: "м²",
    m3: "м³",
  };
  const suffix = suffixMap[unit as keyof typeof suffixMap];
  if (!suffix) {
    return trimmed;
  }
  const lower = trimmed.toLowerCase();
  if (lower.endsWith(suffix) || lower.endsWith(suffix.replace("²", "2"))) {
    return trimmed;
  }
  return `${trimmed} ${suffix}`;
}

export function buildProductDisplayName(name: string, size: string): string {
  const trimmedName = name.trim();
  const trimmedSize = size.trim();
  if (!trimmedSize) {
    return trimmedName;
  }
  return `${trimmedName} ${trimmedSize}`;
}
