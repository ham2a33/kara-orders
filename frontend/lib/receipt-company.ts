import type { InvoiceCompanyPreview } from "@/types/orders";

export type ReceiptCompanySource = Pick<
  InvoiceCompanyPreview,
  | "name"
  | "bin_tax_id"
  | "phone"
  | "email"
  | "website"
  | "address"
  | "instagram"
  | "director_name"
  | "footer_text"
  | "receipt_signature"
  | "invoice_logo_url"
>;

function formatInstagram(value: string | null | undefined): string {
  const cleaned = value?.trim() ?? "";
  if (!cleaned) {
    return "";
  }
  if (cleaned.startsWith("@") || cleaned.includes("instagram.com")) {
    return cleaned;
  }
  return `@${cleaned.replace(/^@+/, "")}`;
}

export function buildReceiptStoreRows(company: ReceiptCompanySource): Array<{ label: string; value: string }> {
  const rows: Array<{ label: string; value: string | null | undefined }> = [
    { label: "БИН", value: company.bin_tax_id },
    { label: "Адрес", value: company.address },
    { label: "Телефон", value: company.phone },
    { label: "Instagram", value: formatInstagram(company.instagram) },
    { label: "Эл. почта", value: company.email },
    { label: "Сайт", value: company.website },
    { label: "Руководитель", value: company.director_name },
  ];
  return rows
    .map((row) => ({ label: row.label, value: row.value?.trim() ?? "" }))
    .filter((row) => row.value.length > 0);
}

export function receiptClosingMessage(company: Pick<ReceiptCompanySource, "footer_text">): string {
  const custom = company.footer_text?.trim();
  return custom && custom.length > 0 ? custom : "Спасибо за покупку!";
}

export function receiptSignature(company: Pick<ReceiptCompanySource, "receipt_signature">): string | null {
  const value = company.receipt_signature?.trim();
  return value && value.length > 0 ? value : null;
}

export function storeDisplayName(company: Pick<ReceiptCompanySource, "name">): string {
  const name = company.name?.trim();
  return name && name.length > 0 ? name : "Магазин";
}
