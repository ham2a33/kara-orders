"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatCount, formatDate, formatMoney, MetricCard, Panel } from "@/components/platform/shared";
import { getOrders } from "@/lib/orders";

function orderStatusLabel(status: string): string {
  switch (status) {
    case "draft":
      return "Черновик";
    case "confirmed":
      return "Подтверждён";
    case "completed":
      return "Выполнен";
    case "cancelled":
      return "Отменён";
    default:
      return status;
  }
}

function orderBadgeVariant(status: string): "default" | "outline" | "success" | "warning" | "danger" {
  if (status === "completed") {
    return "success";
  }
  if (status === "confirmed") {
    return "warning";
  }
  if (status === "cancelled") {
    return "danger";
  }
  return "outline";
}

export default function OrdersPage(): ReactElement {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [sortBy, setSortBy] = useState("created_at");

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    setSearch(new URLSearchParams(window.location.search).get("search") ?? "");
  }, []);

  const ordersQuery = useQuery({
    queryKey: ["orders", search, status, sortBy],
    queryFn: () =>
      getOrders({
        search: search || undefined,
        status: status || undefined,
        sortBy,
      }),
  });

  const orders = useMemo(() => ordersQuery.data?.items ?? [], [ordersQuery.data?.items]);
  const stats = useMemo(
    () => [
      { label: "Черновики", value: formatCount(orders.filter((order) => order.status === "draft").length) },
      { label: "Подтверждены", value: formatCount(orders.filter((order) => order.status === "confirmed").length) },
      { label: "Выполнены", value: formatCount(orders.filter((order) => order.status === "completed").length) },
      { label: "Отменены", value: formatCount(orders.filter((order) => order.status === "cancelled").length) },
    ],
    [orders],
  );

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <Badge>Заказы и счета</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">Заказы</h1>
            <p className="max-w-2xl text-muted-foreground">
              Ручное создание, проверка, сохранение и печать счёта в одном спокойном рабочем пространстве.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/orders/invoices">Счета</Link>
          </Button>
          <Button asChild>
            <Link href="/orders/new">Создать заказ</Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <MetricCard key={stat.label} label={stat.label} value={stat.value} />
        ))}
      </section>

      <Panel title="Последние заказы" description="Поиск, сортировка и фильтрация истории заказов.">
        <div className="grid gap-4 md:grid-cols-3">
          <Input
            placeholder="Поиск заказов"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <select
            className="h-11 rounded-2xl border bg-background px-3 text-sm"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">Все статусы</option>
            <option value="draft">Черновик</option>
            <option value="confirmed">Подтверждён</option>
            <option value="completed">Выполнен</option>
            <option value="cancelled">Отменён</option>
          </select>
          <select
            className="h-11 rounded-2xl border bg-background px-3 text-sm"
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value)}
          >
            <option value="created_at">Сначала новые</option>
            <option value="updated_at">Недавно обновлённые</option>
            <option value="invoice_number">По счёту</option>
            <option value="customer_name">По клиенту</option>
            <option value="total">По сумме</option>
          </select>
        </div>

        <div className="mt-6 grid gap-3 md:hidden">
          {orders.map((order) => (
            <Link key={order.id} href={`/orders/${order.id}`} className="rounded-3xl border p-4 transition-colors hover:bg-muted/40">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <p className="text-sm font-medium">{order.invoice_number}</p>
                  <p className="text-sm text-muted-foreground">{order.customer_name ?? "Без клиента"}</p>
                  <p className="text-xs text-muted-foreground">{formatDate(order.created_at)}</p>
                </div>
                <div className="text-right">
                  <Badge variant={orderBadgeVariant(order.status)}>{orderStatusLabel(order.status)}</Badge>
                  <p className="mt-2 text-sm font-medium">{formatMoney(order.total)}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>

        <div className="mt-6 hidden md:block">
          <table className="w-full text-left text-sm">
            <thead className="border-b text-muted-foreground">
              <tr>
                <th className="py-3 pr-4 font-medium">Счёт</th>
                <th className="py-3 pr-4 font-medium">Клиент</th>
                <th className="py-3 pr-4 font-medium">Статус</th>
                <th className="py-3 pr-4 font-medium">Сумма</th>
                <th className="py-3 font-medium">Дата</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.id} className="border-b last:border-0">
                  <td className="py-4 pr-4 font-medium">
                    <Link className="hover:underline" href={`/orders/${order.id}`}>
                      {order.invoice_number}
                    </Link>
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">{order.customer_name ?? "—"}</td>
                  <td className="py-4 pr-4">
                    <Badge variant={orderBadgeVariant(order.status)}>{orderStatusLabel(order.status)}</Badge>
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">{formatMoney(order.total)}</td>
                  <td className="py-4 text-muted-foreground">{formatDate(order.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
