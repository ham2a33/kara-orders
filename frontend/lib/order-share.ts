import { buildHeaders, resolveUrl } from "@/lib/api-client";
import { formatMoney } from "@/components/platform/shared";
import { receiptSignature, storeDisplayName } from "@/lib/receipt-company";
import type { Order } from "@/types/orders";

export type WhatsAppShareMode = "wa_me" | "cloud_api";

export type OrderShareConfig = {
  whatsappMode?: WhatsAppShareMode;
};

const pdfBlobCache = new Map<string, Blob>();

function readShareConfig(): OrderShareConfig {
  const mode = process.env.NEXT_PUBLIC_WHATSAPP_MODE;
  if (mode === "cloud_api") {
    return { whatsappMode: "cloud_api" };
  }
  return { whatsappMode: "wa_me" };
}

export type ShareCompanySource = {
  name: string;
  welcome_message?: string | null;
  receipt_signature?: string | null;
  currency?: string | null;
};

export function buildReceiptPublicUrl(orderId: string): string {
  if (typeof window === "undefined") {
    return `/orders/${orderId}/invoice`;
  }
  return new URL(`/orders/${orderId}/invoice`, window.location.origin).toString();
}

export function normalizeWhatsAppPhone(raw: string | null | undefined): string | null {
  const digits = (raw ?? "").replace(/\D/g, "");
  if (!digits) {
    return null;
  }
  if (digits.length === 11 && digits.startsWith("8")) {
    return `7${digits.slice(1)}`;
  }
  if (digits.length === 10) {
    return `7${digits}`;
  }
  return digits;
}

export function buildWhatsAppReceiptMessage(order: Order, company: ShareCompanySource): string {
  const storeName = storeDisplayName(company);
  const currency = company.currency ?? "KZT";
  const total = formatMoney(order.total, currency);
  const welcome = company.welcome_message?.trim();
  const signature = receiptSignature({ receipt_signature: company.receipt_signature ?? null })?.replace(/\r\n/g, "\n") ?? `С уважением,\nМагазин «${storeName}»`;

  if (welcome) {
    return [
      welcome,
      "",
      `Ваш заказ №${order.invoice_number} успешно оформлен.`,
      "",
      "Сумма:",
      total,
      "",
      "Во вложении находится электронный чек.",
      "",
      signature,
    ].join("\n");
  }

  return [
    "Здравствуйте!",
    "",
    `Спасибо за покупку в магазине «${storeName}».`,
    "",
    `Ваш заказ №${order.invoice_number} успешно оформлен.`,
    "",
    "Сумма:",
    total,
    "",
    "Во вложении находится электронный чек.",
    "",
    signature,
  ].join("\n");
}

export async function fetchOrderReceiptPdfBlob(orderId: string): Promise<Blob> {
  const cached = pdfBlobCache.get(orderId);
  if (cached) {
    return cached;
  }

  const response = await fetch(resolveUrl(`/orders/${orderId}/invoice/pdf`), {
    method: "GET",
    headers: buildHeaders(),
    credentials: "include",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Не удалось загрузить PDF чека");
  }

  const blob = await response.blob();
  pdfBlobCache.set(orderId, blob);
  return blob;
}

export async function downloadOrderReceiptPdf(orderId: string, invoiceNumber: string): Promise<Blob> {
  const blob = await fetchOrderReceiptPdfBlob(orderId);
  if (typeof window === "undefined") {
    return blob;
  }

  const objectUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = `receipt-${invoiceNumber}.pdf`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(objectUrl);
  return blob;
}

function openWhatsAppWaMe(phone: string, message: string): void {
  const url = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
  window.open(url, "_blank", "noopener,noreferrer");
}

async function shareViaWhatsAppCloudApi(_order: Order, _company: ShareCompanySource, _phone: string): Promise<void> {
  throw new Error("WhatsApp Cloud API ещё не подключён. Установите NEXT_PUBLIC_WHATSAPP_MODE=wa_me.");
}

export async function shareViaWhatsApp(params: {
  order: Order;
  company: ShareCompanySource;
  customerPhone: string | null | undefined;
  config?: OrderShareConfig;
}): Promise<void> {
  const phone = normalizeWhatsAppPhone(params.customerPhone);
  if (!phone) {
    throw new Error("У покупателя не указан номер телефона.");
  }

  const mode = params.config?.whatsappMode ?? readShareConfig().whatsappMode ?? "wa_me";
  const message = buildWhatsAppReceiptMessage(params.order, params.company);

  await downloadOrderReceiptPdf(params.order.id, params.order.invoice_number);

  if (mode === "cloud_api") {
    await shareViaWhatsAppCloudApi(params.order, params.company, phone);
    return;
  }

  openWhatsAppWaMe(phone, message);
}

export async function shareViaTelegram(params: {
  order: Order;
  company: ShareCompanySource;
  customerPhone?: string | null;
}): Promise<void> {
  const message = buildWhatsAppReceiptMessage(params.order, params.company);
  const url = `https://t.me/share/url?url=${encodeURIComponent(buildReceiptPublicUrl(params.order.id))}&text=${encodeURIComponent(message)}`;
  window.open(url, "_blank", "noopener,noreferrer");
}

export async function copyReceiptLink(orderId: string): Promise<string> {
  const link = buildReceiptPublicUrl(orderId);
  if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(link);
  }
  return link;
}

export function printOrderReceipt(orderId: string): void {
  const url = buildReceiptPublicUrl(orderId);
  const printWindow = window.open(url, "_blank", "noopener,noreferrer");
  if (!printWindow) {
    window.location.assign(url);
  }
}

export function clearReceiptPdfCache(orderId?: string): void {
  if (orderId) {
    pdfBlobCache.delete(orderId);
    return;
  }
  pdfBlobCache.clear();
}
