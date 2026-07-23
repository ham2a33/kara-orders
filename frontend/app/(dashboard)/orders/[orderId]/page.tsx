"use client";

import Link from "next/link";
import { useMemo, type ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { deleteOrder, getOrder, restoreOrder } from "@/lib/orders";
import { extractErrorMessage } from "@/lib/errors";
import { formatDate, formatMoney } from "@/components/platform/shared";
import { orderStatusLabel } from "@/lib/order-statuses";

export default function OrderDetailsPage(): ReactElement {
  const params = useParams<{ orderId: string }>();
  const orderId = params.orderId;
  const router = useRouter();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["order", orderId],
    queryFn: () => getOrder(orderId),
    enabled: Boolean(orderId),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteOrder,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["orders"] });
      await queryClient.invalidateQueries({ queryKey: ["order", orderId] });
      router.push("/orders");
    },
  });
  const restoreMutation = useMutation({
    mutationFn: restoreOrder,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["orders"] });
      await queryClient.invalidateQueries({ queryKey: ["order", orderId] });
    },
  });

  const order = query.data;
  const items = order?.items ?? [];
  const metrics = useMemo(
    () => [
      { label: "Статус", value: order ? orderStatusLabel(order.status) : "—" },
      { label: "Промежуточная сумма", value: formatMoney(order?.subtotal ?? "0") },
      { label: "Налог", value: formatMoney(order?.tax_total ?? "0") },
      { label: "Итого", value: formatMoney(order?.total ?? "0") },
    ],
    [order],
  );

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <Badge>Детали заказа</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">{order?.invoice_number ?? orderId}</h1>
            <p className="max-w-2xl text-muted-foreground">
              Заказ {orderId} с позициями, рассчитанными суммами и действиями по счёту.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/orders">К заказам</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href={`/orders/${orderId}/edit`}>Редактировать заказ</Link>
          </Button>
          <Button asChild>
            <Link href={`/orders/${orderId}/invoice`}>Предпросмотр счёта</Link>
          </Button>
          {order?.deleted_at ? (
            <Button type="button" onClick={() => restoreMutation.mutate(orderId)} disabled={restoreMutation.isPending}>
              Восстановить
            </Button>
          ) : (
            <Button type="button" variant="secondary" onClick={() => deleteMutation.mutate(orderId)} disabled={deleteMutation.isPending}>
              Удалить
            </Button>
          )}
        </div>
      </section>

      {query.isError ? (
        <Card className="border-destructive/30">
          <CardContent className="p-5 text-sm text-destructive">{extractErrorMessage(query.error)}</CardContent>
        </Card>
      ) : null}

      <section className="grid gap-4 md:grid-cols-4">
        {metrics.map((metric) => (
            <Card key={metric.label}>
              <CardHeader>
                <CardDescription>{metric.label}</CardDescription>
                <CardTitle className="text-3xl">{metric.value}</CardTitle>
              </CardHeader>
            </Card>
          ))}
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <CardHeader>
          <CardTitle>Позиции</CardTitle>
          <CardDescription>Проверьте строки заказа ровно так, как их отрендерит движок счёта.</CardDescription>
          </CardHeader>
          <CardContent className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-left text-sm">
                <thead className="border-b text-muted-foreground">
                  <tr>
                    <th className="py-3 pr-4 font-medium">Товар</th>
                    <th className="py-3 pr-4 font-medium">Кол-во</th>
                    <th className="py-3 pr-4 font-medium">Цена</th>
                    <th className="py-3 pr-4 font-medium">Скидка</th>
                    <th className="py-3 pr-4 font-medium">Налог</th>
                    <th className="py-3 font-medium">Итого</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id} className="border-b last:border-0">
                      <td className="py-4 pr-4 font-medium">{item.product_name}</td>
                      <td className="py-4 pr-4 text-muted-foreground">{item.quantity}</td>
                      <td className="py-4 pr-4 text-muted-foreground">{formatMoney(item.unit_price)}</td>
                      <td className="py-4 pr-4 text-muted-foreground">{formatMoney(item.discount_amount)}</td>
                      <td className="py-4 pr-4 text-muted-foreground">{formatMoney(item.tax_amount)}</td>
                      <td className="py-4 text-muted-foreground">{formatMoney(item.line_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
          <CardTitle>Клиент и счёт</CardTitle>
          <CardDescription>Вся информация для счёта собрана в одном аккуратном блоке.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>Клиент: {order?.customer_name ?? "—"}</p>
            <p>Телефон: {order?.customer_phone ?? "—"}</p>
            <p>Адрес: {order?.customer_address ?? "—"}</p>
            <p>Комментарий: {order?.notes ?? "—"}</p>
            <p>Создан: {formatDate(order?.created_at ?? null)}</p>
            <p>Обновлён: {formatDate(order?.updated_at ?? null)}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
