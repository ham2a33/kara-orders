"use client";

import Link from "next/link";
import { useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiDownload } from "@/lib/api-client";
import { getInvoicePreview } from "@/lib/orders";
import { formatMoney } from "@/components/platform/shared";
import { extractErrorMessage } from "@/lib/errors";

export default function OrderInvoicePage(): ReactElement {
  const params = useParams<{ orderId: string }>();
  const orderId = params.orderId;
  const [isDownloading, setIsDownloading] = useState(false);
  const query = useQuery({
    queryKey: ["order-invoice", orderId],
    queryFn: () => getInvoicePreview(orderId),
    enabled: Boolean(orderId),
  });

  const downloadPdf = async (): Promise<void> => {
    setIsDownloading(true);
    try {
      await apiDownload(`/orders/${orderId}/invoice/pdf`, `invoice-${orderId}.pdf`);
    } finally {
      setIsDownloading(false);
    }
  };

  const preview = query.data;
  const order = preview?.order;

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <Badge>Предпросмотр счёта</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">PDF счёта</h1>
            <p className="max-w-2xl text-muted-foreground">
              Посмотрите профессиональный счёт для заказа {orderId}, а затем скачайте или распечатайте его напрямую.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button type="button" variant="outline" onClick={downloadPdf} disabled={isDownloading}>
            {isDownloading ? "Скачиваем..." : "Скачать PDF"}
          </Button>
          <Button type="button" onClick={downloadPdf} disabled={isDownloading}>
            {isDownloading ? "Генерируем..." : "Печать / пересоздание"}
          </Button>
        </div>
      </section>

      {query.isError ? (
        <Card className="border-destructive/30">
          <CardContent className="p-5 text-sm text-destructive">{extractErrorMessage(query.error)}</CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="min-h-[720px]">
          <CardHeader>
            <CardTitle>Полотно счёта</CardTitle>
            <CardDescription>Стилизовано так же, как production PDF-вывод.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="rounded-3xl border bg-muted/20 p-6">
              <div className="mb-6 flex items-start justify-between gap-6">
                <div>
                  <p className="text-sm text-muted-foreground">{preview?.company_name ?? "Компания"}</p>
                  <h2 className="text-2xl font-semibold tracking-tight">{order?.invoice_number ?? `Order ${orderId}`}</h2>
                  <p className="text-sm text-muted-foreground">
                    Дата: {order ? new Date(order.created_at).toLocaleDateString("ru-RU") : "—"}
                  </p>
                </div>
                <Badge variant="success">{order?.status ?? "Готово"}</Badge>
              </div>
              <div className="grid gap-6 md:grid-cols-2">
                <div>
                  <p className="text-sm font-medium">Информация о компании</p>
                  <p className="text-sm text-muted-foreground">{preview?.company_name ?? "—"}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Информация о клиенте</p>
                  <p className="text-sm text-muted-foreground">{order?.customer_name ?? "—"}</p>
                  <p className="text-sm text-muted-foreground">{order?.customer_phone ?? "—"}</p>
                  <p className="text-sm text-muted-foreground">{order?.customer_address ?? "—"}</p>
                </div>
              </div>
              <div className="mt-6 overflow-hidden rounded-2xl border bg-background">
                <table className="w-full text-left text-sm">
                  <thead className="border-b bg-muted/30 text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3 font-medium">Товар</th>
                      <th className="px-4 py-3 font-medium">Кол-во</th>
                      <th className="px-4 py-3 font-medium">Итого</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(order?.items ?? []).map((item) => (
                      <tr key={item.id} className="border-b last:border-0">
                        <td className="px-4 py-3">{item.product_name}</td>
                        <td className="px-4 py-3">{item.quantity}</td>
                        <td className="px-4 py-3">{formatMoney(item.line_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="rounded-3xl border bg-background p-6 text-sm text-muted-foreground">
              Backend-генератор PDF создаёт финальный счёт с итогами, футером и платёжной информацией.
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Действия со счётом</CardTitle>
            <CardDescription>Скачайте, распечатайте или заново сгенерируйте счёт.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border bg-muted/30 p-4">
              <p className="text-sm font-medium">Скачивание PDF</p>
              <p className="text-sm text-muted-foreground">Использует backend endpoint `/invoice/pdf` с auth-заголовками.</p>
            </div>
            <div className="rounded-2xl border bg-muted/30 p-4">
              <p className="text-sm font-medium">Печать</p>
              <p className="text-sm text-muted-foreground">Печать в браузере использует тот же PDF-вывод.</p>
            </div>
            <div className="rounded-2xl border bg-muted/30 p-4">
              <p className="text-sm font-medium">Пересоздание</p>
              <p className="text-sm text-muted-foreground">Счёт пересоздаётся из текущих данных заказа по запросу.</p>
            </div>
            <Button asChild variant="outline" className="w-full">
              <Link href={`/orders/${orderId}`}>Назад к заказу</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
