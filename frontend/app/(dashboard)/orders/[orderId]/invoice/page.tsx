"use client";

import Link from "next/link";
import { useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { ReceiptPreview } from "@/components/orders/receipt-preview";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiDownload } from "@/lib/api-client";
import { getInvoicePreview } from "@/lib/orders";
import { extractErrorMessage } from "@/lib/errors";
import { orderStatusBadgeVariant, orderStatusLabel } from "@/lib/order-statuses";

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
      await apiDownload(`/orders/${orderId}/invoice/pdf`, `receipt-${orderId}.pdf`);
    } finally {
      setIsDownloading(false);
    }
  };

  const preview = query.data;
  const order = preview?.order;
  const company = preview?.company;

  return (
    <div className="space-y-6 print:space-y-0">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between print:hidden">
        <div className="space-y-3">
          <Badge>Товарный чек</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">Печать чека</h1>
            <p className="max-w-2xl text-muted-foreground">
              Предпросмотр товарного чека для заказа {orderId}. PDF совпадает с макетом ниже.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button type="button" variant="outline" onClick={downloadPdf} disabled={isDownloading}>
            {isDownloading ? "Скачиваем..." : "Скачать PDF"}
          </Button>
          <Button type="button" onClick={() => window.print()} disabled={!order || !company}>
            Печать
          </Button>
        </div>
      </section>

      {query.isError ? (
        <Card className="border-destructive/30 print:hidden">
          <CardContent className="p-5 text-sm text-destructive">{extractErrorMessage(query.error)}</CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr] print:block">
        <Card className="min-h-[720px] print:min-h-0 print:border-0 print:shadow-none">
          <CardHeader className="print:hidden">
            <CardTitle>Макет чека</CardTitle>
            <CardDescription>Узкая вёрстка для 58/80 мм и печати на A4.</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center print:p-0">
            <div className="w-full max-w-[80mm] rounded-3xl border bg-white p-6 shadow-sm print:max-w-none print:rounded-none print:border-0 print:p-0 print:shadow-none">
              {order && company ? (
                <ReceiptPreview order={order} company={company} />
              ) : (
                <p className="text-sm text-muted-foreground">Загружаем чек...</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="print:hidden">
          <CardHeader>
            <CardTitle>Действия</CardTitle>
            <CardDescription>Статус заказа и быстрые ссылки.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border bg-muted/30 p-4">
              <p className="text-sm font-medium">Статус заказа</p>
              <div className="mt-2">
                <Badge variant={order ? orderStatusBadgeVariant(order.status) : "outline"}>
                  {order ? orderStatusLabel(order.status) : "—"}
                </Badge>
              </div>
            </div>
            <div className="rounded-2xl border bg-muted/30 p-4">
              <p className="text-sm font-medium">PDF</p>
              <p className="text-sm text-muted-foreground">Генерируется на backend тем же шаблоном, что и предпросмотр.</p>
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
