import type { Product } from "@/types/products";

/** Canonical units used in the manual order UI (display labels in Russian). */
export const ORDER_UNIT_OPTIONS = [
  { value: "pcs", label: "шт" },
  { value: "m", label: "м" },
  { value: "kg", label: "кг" },
  { value: "l", label: "л" },
  { value: "m2", label: "м²" },
  { value: "m3", label: "м³" },
] as const;

export type OrderUnitValue = (typeof ORDER_UNIT_OPTIONS)[number]["value"];

const METER_NAME_HINTS = [
  "труб",
  "труба",
  "арматур",
  "профил",
  "кабел",
  "кабель",
  "уголок",
  "швеллер",
  "рейк",
  "брус",
  "прут",
  "штанг",
  "провод",
  "круг ",
  "полос",
];

const PIECE_NAME_HINTS = [
  "ведро",
  "клей",
  "саморез",
  "краск",
  "мешок",
  "перчат",
  "рулон",
  "банка",
  "туба",
  "упак",
];

function normalizeForMatch(value: string): string {
  return value.trim().toLowerCase().replace(/ё/g, "е");
}

function catalogUnitToOrderUnit(raw: string | null | undefined): OrderUnitValue {
  const unit = normalizeForMatch(raw ?? "");
  if (!unit) {
    return "pcs";
  }
  if (unit === "pcs" || unit === "pc" || unit === "piece" || unit === "шт" || unit === "штук") {
    return "pcs";
  }
  if (unit === "m" || unit === "meter" || unit === "metre" || unit === "м" || unit === "метр") {
    return "m";
  }
  if (unit === "kg" || unit === "kilogram" || unit === "кг" || unit === "кило") {
    return "kg";
  }
  if (unit === "l" || unit === "liter" || unit === "litre" || unit === "л" || unit === "литр") {
    return "l";
  }
  if (unit === "m2" || unit === "m²" || unit === "sqm" || unit === "м2" || unit === "м²") {
    return "m2";
  }
  if (unit === "m3" || unit === "m³" || unit === "cbm" || unit === "м3" || unit === "м³") {
    return "m3";
  }
  return "pcs";
}

export function orderUnitLabel(unit: OrderUnitValue): string {
  return ORDER_UNIT_OPTIONS.find((option) => option.value === unit)?.label ?? "шт";
}

export function resolveOrderUnit(product: Product): OrderUnitValue {
  const haystack = normalizeForMatch(
    [product.name, product.category ?? "", product.description ?? "", product.aliases.join(" ")].join(" "),
  );

  if (METER_NAME_HINTS.some((hint) => haystack.includes(hint))) {
    return "m";
  }
  if (PIECE_NAME_HINTS.some((hint) => haystack.includes(hint))) {
    return "pcs";
  }
  return catalogUnitToOrderUnit(product.unit);
}

export function quantityStepForUnit(unit: OrderUnitValue): string {
  return unit === "pcs" ? "1" : "0.1";
}

export function parseQuantityInput(raw: string): number | null {
  const normalized = raw.trim().replace(",", ".");
  if (!normalized) {
    return null;
  }
  const value = Number(normalized);
  if (!Number.isFinite(value) || value <= 0) {
    return null;
  }
  return value;
}
