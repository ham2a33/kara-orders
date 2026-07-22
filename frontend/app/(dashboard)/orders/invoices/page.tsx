"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getOrders } from "@/lib/orders";
import { formatMoney } from "@/components/platform/shared";

export default function InvoiceListPage(): ReactElement {
  const query = useQuery({
    queryKey: ["invoice-queue"],
    queryFn: () => getOrders({ sortBy: "created_at", sortDir: "desc" }),
  });

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <Badge>Предпросмотр счёта</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Очередь счетов</h1>
        <p className="max-w-2xl text-muted-foreground">
          Лёгкий список для поиска заказов, скачивания PDF и печати счетов по требованию.
        </p>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Последние счета</CardTitle>
          <CardDescription>Каждый счёт создаётся на сервере из последних подтверждённых данных заказа.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {(query.data?.items ?? []).map((invoice) => (
            <div key={invoice.id} className="flex items-center justify-between rounded-2xl border px-4 py-3">
              <div>
                <p className="font-medium">{invoice.invoice_number}</p>
                <p className="text-sm text-muted-foreground">
                  {invoice.customer_name ?? "—"} · {new Date(invoice.created_at).toLocaleDateString("ru-RU")}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <p className="text-sm text-muted-foreground">{formatMoney(invoice.total)}</p>
                <Button asChild size="sm" variant="outline">
                  <Link href={`/orders/${invoice.id}/invoice`}>Открыть</Link>
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
