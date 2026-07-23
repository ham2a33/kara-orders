"use client";

import Link from "next/link";
import { useMemo, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  CalendarClock,
  Clock3,
  ReceiptText,
  Sparkles,
  Trash2,
  TrendingUp,
  TriangleAlert,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { getAIRecognitions } from "@/lib/ai";
import { getAuditLogs } from "@/lib/platform";
import { getCurrentSession } from "@/lib/session";
import { getDashboardAnalytics, getOrdersAnalytics } from "@/lib/analytics";
import { formatCount, formatDate, formatMoney, Panel, MetricCard } from "@/components/platform/shared";
import { quickActions } from "@/components/navigation/nav-config";
import { orderStatusBadgeVariant, orderStatusLabel } from "@/lib/order-statuses";

function timeGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 6) {
    return "Доброй ночи";
  }
  if (hour < 12) {
    return "Доброе утро";
  }
  if (hour < 18) {
    return "Добрый день";
  }
  return "Добрый вечер";
}

function aiStatusLabel(status: string): string {
  switch (status) {
    case "completed":
      return "Готово";
    case "needs_review":
      return "Требует проверки";
    case "failed":
      return "Ошибка";
    case "converted":
      return "Преобразовано";
    default:
      return status;
  }
}

function actionLabel(action: string): string {
  const dictionary: Record<string, string> = {
    login: "Вход",
    role_changed: "Роль изменена",
    company_updated: "Компания обновлена",
    plan_changed: "План изменён",
    ai_request: "AI-запрос",
    order_created: "Заказ создан",
    product_updated: "Товар обновлён",
  };
  return dictionary[action] ?? action.replaceAll("_", " ");
}

export function DashboardClient(): ReactElement {
  const sessionQuery = useQuery({
    queryKey: ["session-me-home"],
    queryFn: getCurrentSession,
  });
  const dashboardQuery = useQuery({
    queryKey: ["dashboard-home", "today"],
    queryFn: () => getDashboardAnalytics({ preset: "today" }),
  });
  const ordersQuery = useQuery({
    queryKey: ["orders-home", "today"],
    queryFn: () => getOrdersAnalytics({ preset: "today" }),
  });
  const aiQuery = useQuery({
    queryKey: ["ai-home", "latest"],
    queryFn: () => getAIRecognitions({ pageSize: 5 }),
  });
  const auditQuery = useQuery({
    queryKey: ["audit-home", "latest"],
    queryFn: () => getAuditLogs({ pageSize: 5 }),
  });

  const greeting = timeGreeting();
  const personName = sessionQuery.data?.user.full_name ?? sessionQuery.data?.user.email ?? "Команда";

  const quickCards = useMemo(
    () =>
      quickActions.map((item, index) => {
        const Icon = item.icon;
        const tone =
          index === 0 ? "from-blue-500/20 to-sky-500/10" : index === 1 ? "from-emerald-500/20 to-lime-500/10" : "from-violet-500/20 to-fuchsia-500/10";
        return (
          <Link key={item.href} href={item.href} className="group">
            <Card className="h-full overflow-hidden border-transparent bg-gradient-to-br shadow-soft transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg">
              <CardContent className={`flex h-full flex-col justify-between gap-6 bg-gradient-to-br p-6 ${tone}`}>
                <div className="flex items-center justify-between">
                  <div className="flex h-14 w-14 items-center justify-center rounded-3xl bg-background/80 text-primary shadow-sm backdrop-blur">
                    <Icon className="h-6 w-6" />
                  </div>
                  <ArrowRight className="h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-2xl font-semibold tracking-tight">{item.label}</h2>
                  <p className="max-w-xs text-sm text-muted-foreground">
                    {item.href === "/orders/new"
                      ? "Сразу перейти к созданию вручную или через AI-поток."
                      : item.href === "/products/new"
                        ? "Добавить товар в каталог и продолжить работу без задержек."
                        : "Открыть рабочий сценарий без лишних переходов."}
                  </p>
                </div>
              </CardContent>
            </Card>
          </Link>
        );
      }),
    [],
  );

  const stats = dashboardQuery.data && ordersQuery.data
    ? [
        { label: "Сегодня заказов", value: formatCount(dashboardQuery.data.metrics.today_orders), icon: ReceiptText },
        { label: "Выручка за сегодня", value: formatMoney(dashboardQuery.data.metrics.today_revenue), icon: TrendingUp },
        { label: "Средний чек", value: formatMoney(dashboardQuery.data.metrics.average_invoice), icon: Clock3 },
        {
          label: "Товаров с низким остатком",
          value: formatCount(dashboardQuery.data.metrics.low_stock_products),
          icon: TriangleAlert,
          description: "Следите за запасами до того, как товар закончится.",
        },
        {
          label: "Новые",
          value: formatCount(ordersQuery.data.status_breakdown.new_orders),
          icon: CalendarClock,
          description: "Новые заказы в текущем периоде.",
        },
        {
          label: "Подтвержденные",
          value: formatCount(ordersQuery.data.status_breakdown.confirmed_orders),
          icon: Sparkles,
          description: "Подтвержденные заказы в текущем периоде.",
        },
        {
          label: "Удаленные",
          value: formatCount(ordersQuery.data.status_breakdown.deleted_orders),
          icon: Trash2,
          description: "Удаленные заказы в текущем периоде.",
        },
      ]
    : [];

  return (
    <div className="flex flex-col gap-6">
      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="overflow-hidden border-transparent bg-gradient-to-br from-primary/10 via-background to-background shadow-soft">
          <CardContent className="flex h-full flex-col justify-between gap-8 p-6 sm:p-8">
            <div className="space-y-4">
              <Badge className="rounded-full bg-primary/10 px-3 py-1 text-primary">Kara Orders</Badge>
              <div className="space-y-3">
                <p className="text-sm font-medium text-muted-foreground">{greeting}, {personName} 👋</p>
                <h1 className="max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
                  Управляйте заказами, каталогом и аналитикой в одном чистом рабочем пространстве.
                </h1>
                <p className="max-w-2xl text-base text-muted-foreground sm:text-lg">
                  Всё загружается из реального backend: заказы, товары, AI-распознавания, аудит и финансовая аналитика.
                </p>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              {quickActions.map((item) => {
                const Icon = item.icon;
                return (
                  <Button key={item.href} asChild size="lg" className="h-16 justify-start rounded-3xl px-5">
                    <Link href={item.href}>
                      <Icon className="h-5 w-5" />
                      {item.label}
                    </Link>
                  </Button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1">
          {stats.slice(0, 3).map((stat) => {
            const Icon = stat.icon;
            return (
              <Card key={stat.label} className="shadow-soft">
                <CardContent className="flex items-center justify-between gap-4 p-5">
                  <div>
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                    <p className="mt-1 text-2xl font-semibold tracking-tight">{stat.value}</p>
                  </div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-muted/60 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {quickCards}
      </section>

      {dashboardQuery.data ? (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {stats.slice(3).map((stat) => {
            return (
              <MetricCard
                key={stat.label}
                label={stat.label}
                value={stat.value}
                description={stat.description}
              />
            );
          })}
        </section>
      ) : null}

      {dashboardQuery.data ? (
        <section className="grid gap-6 xl:grid-cols-2">
          <Panel title="Последние заказы" description="Свежее движение по заказам из API.">
            <div className="flex flex-col gap-3">
              {dashboardQuery.data.recent_orders.slice(0, 6).map((order) => (
                <Link key={order.id} href={`/orders/${order.id}`} className="rounded-2xl border p-4 transition-colors hover:bg-muted/40">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-medium">{order.customer_name ?? "Без клиента"}</p>
                      <p className="text-sm text-muted-foreground">
                        {order.invoice_number} • {formatDate(order.created_at)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">{formatMoney(order.total)}</p>
                      <Badge variant={orderStatusBadgeVariant(order.status)} className="mt-2">
                        {orderStatusLabel(order.status)}
                      </Badge>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </Panel>

          <Panel title="Последние действия AI" description="История распознаваний за последние записи.">
            <div className="flex flex-col gap-3">
              {aiQuery.data?.items.slice(0, 5).map((recognition) => (
                <Link key={recognition.id} href={`/ai/review/${recognition.id}`} className="rounded-2xl border p-4 transition-colors hover:bg-muted/40">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-medium capitalize">{recognition.input_type}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatDate(recognition.created_at)} • {recognition.items.length} поз.
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">{aiStatusLabel(recognition.status)}</p>
                      <p className="text-sm text-muted-foreground">
                        {recognition.confidence ? `Уверенность ${Number(recognition.confidence).toFixed(2)}` : "Без оценки"}
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </Panel>
        </section>
      ) : null}

      {auditQuery.data ? (
        <Panel title="Последняя активность" description="Аудит-лог компании и системные события.">
          <div className="grid gap-3">
            {auditQuery.data.items.map((entry) => (
              <div key={entry.id} className="rounded-2xl border p-4">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-medium">{actionLabel(entry.action)}</p>
                    <p className="text-sm text-muted-foreground">
                      {entry.description ?? "—"} • {formatDate(entry.created_at)}
                    </p>
                  </div>
                  <Badge variant="outline">{entry.resource_type ?? "system"}</Badge>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      ) : null}
    </div>
  );
}
