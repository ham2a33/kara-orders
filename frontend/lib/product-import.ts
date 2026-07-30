import { apiClient } from "@/lib/api-client";
import type {
  ImportSource,
  ProductImportConfirmResponse,
  ProductImportParseResponse,
  ProductImportRow,
} from "@/types/product-import";

const PARSE_ENDPOINTS: Record<ImportSource, string> = {
  excel: "/products/import/parse-excel",
  pdf: "/products/import/parse-pdf",
  photo: "/products/import/parse-photo",
};

export async function parseImportFile(source: ImportSource, file: File): Promise<ProductImportParseResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient<ProductImportParseResponse>(PARSE_ENDPOINTS[source], {
    method: "POST",
    body: formData,
  });
}

export async function confirmProductImport(rows: ProductImportRow[]): Promise<ProductImportConfirmResponse> {
  return apiClient<ProductImportConfirmResponse>("/products/import/confirm", {
    method: "POST",
    body: { rows },
  });
}
