export type ProductImportRow = {
  name: string;
  price: string | number;
  category?: string | null;
  manufacturer?: string | null;
  size?: string | null;
};

export type ProductImportParseResponse = {
  columns: string[];
  mapping: Record<string, string | null>;
  rows: ProductImportRow[];
};

export type ProductImportConfirmResponse = {
  created: number;
  errors: Array<{
    row_index: number;
    name: string;
    message: string;
  }>;
};

export type ImportSource = "excel" | "pdf" | "photo";

export const IMPORT_FIELD_LABELS: Record<string, string> = {
  name: "Название товара",
  price: "Цена продажи",
  category: "Категория",
  manufacturer: "Производитель",
  size: "Размер",
};

export const IMPORT_SOURCE_LABELS: Record<ImportSource, string> = {
  excel: "Excel / CSV",
  pdf: "PDF",
  photo: "Фото",
};

export const IMPORT_ACCEPT: Record<ImportSource, string> = {
  excel: ".xlsx,.csv",
  pdf: ".pdf",
  photo: ".png,.jpg,.jpeg,.webp",
};
