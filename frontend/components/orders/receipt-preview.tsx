"use client";

import Image from "next/image";
import type { ReactElement } from "react";

import { formatMoney } from "@/components/platform/shared";
import {
  buildReceiptStoreRows,
  receiptClosingMessage,
  receiptSignature,
  storeDisplayName,
} from "@/lib/receipt-company";
import type { InvoiceCompanyPreview, Order } from "@/types/orders";

type ReceiptPreviewProps = {
  order: Order;
  company: InvoiceCompanyPreview;
};

function formatReceiptDate(isoDate: string, timezone: string): string {
  try {
    return new Intl.DateTimeFormat("ru-RU", {
      timeZone: timezone,
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(isoDate));
  } catch {
    return new Date(isoDate).toLocaleString("ru-RU");
  }
}

function formatTaxRate(value: string): string {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return value;
  }
  return Number.isInteger(numeric) ? String(numeric) : String(numeric);
}

function ReceiptRule(): ReactElement {
  return <div className="my-4 border-t border-dashed border-muted-foreground/50" />;
}

export function ReceiptPreview({ order, company }: ReceiptPreviewProps): ReactElement {
  const currency = company.currency || "KZT";
  const storeRows = buildReceiptStoreRows(company);
  const vatRate = formatTaxRate(company.tax_percentage);
  const closing = receiptClosingMessage(company);
  const signature = receiptSignature(company);
  const logoUrl = company.invoice_logo_url?.trim();

  return (
    <article className="receipt-preview mx-auto w-full max-w-[80mm] font-mono text-[11px] leading-relaxed text-foreground print:max-w-[80mm]">
      <header className="text-center">
        {logoUrl ? (
          <div className="relative mx-auto mb-3 h-12 w-32">
            <Image src={logoUrl} alt="" fill className="object-contain" unoptimized />
          </div>
        ) : null}
        <p className="text-sm font-bold tracking-wide">{storeDisplayName(company)}</p>
      </header>

      {storeRows.length > 0 ? (
        <section className="mt-4 space-y-2">
          {storeRows.map((row) => (
            <p key={row.label}>
              <span className="text-muted-foreground">{row.label}:</span>
              <br />
              {row.value}
            </p>
          ))}
        </section>
      ) : null}

      <ReceiptRule />

      <section className="text-center">
        <p className="font-semibold">Товарный чек №{order.invoice_number}</p>
      </section>

      <section className="mt-4 space-y-1">
        <p>
          <span className="text-muted-foreground">Дата:</span>
          <br />
          {formatReceiptDate(order.created_at, company.timezone)}
        </p>
      </section>

      {order.customer_name?.trim() ? (
        <section className="mt-4">
          <p>
            <span className="text-muted-foreground">Покупатель:</span>
            <br />
            {order.customer_name.trim()}
          </p>
        </section>
      ) : null}

      <ReceiptRule />

      <section className="mt-5 space-y-4">
        {order.items.map((item) => (
          <div key={item.id}>
            <p className="font-medium">{item.product_name}</p>
            <div className="mt-0.5 flex items-start justify-between gap-3 text-muted-foreground">
              <span>
                {item.quantity} × {formatMoney(item.unit_price, currency)}
              </span>
              <span className="shrink-0 text-foreground">{formatMoney(item.line_total, currency)}</span>
            </div>
          </div>
        ))}
      </section>

      <ReceiptRule />

      <section className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span>Подытог</span>
          <span>{formatMoney(order.subtotal, currency)}</span>
        </div>
        {Number(order.discount_total) > 0 ? (
          <div className="flex items-center justify-between">
            <span>Скидка</span>
            <span>{formatMoney(order.discount_total, currency)}</span>
          </div>
        ) : null}
        <div className="flex items-center justify-between">
          <span>НДС ({vatRate}%)</span>
          <span>{formatMoney(order.tax_total, currency)}</span>
        </div>
        <div className="flex items-center justify-between border-t border-foreground pt-2 text-sm font-bold">
          <span>ИТОГО</span>
          <span>{formatMoney(order.total, currency)}</span>
        </div>
      </section>

      <ReceiptRule />

      <p className="whitespace-pre-line text-center text-xs">{closing}</p>
      {signature ? <p className="mt-4 whitespace-pre-line text-center text-xs">{signature}</p> : null}
    </article>
  );
}
