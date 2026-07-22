"use client";

import { AlertCircle, Download, FileSpreadsheet, FileText, Layers3, PackageSearch, TrendingUp } from "lucide-react";
import { useMemo, useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  downloadAnalyticsExport,
  getCustomersAnalytics,
  getOrdersAnalytics,
  getProductsAnalytics,
  getRevenueAnalytics,
} from "@/lib/analytics";
import {
  analyticsPresets,
  formatCount,
  formatMoney,
  MetricCard,
  Panel,
  SectionBadge,
  SegmentControl,
} from "@/components/analytics/shared";
import type { AnalyticsPreset, AnalyticsSeriesPoint } from "@/types/analytics";

type RangeMode = AnalyticsPreset | "custom";

const analyticsRangeOptions = [...analyticsPresets, { value: "custom", label: "Custom range" }] as const;

function parseSeries(points: AnalyticsSeriesPoint[]): Array<{ label: string; value: number }> {
  return points.map((point) => ({ label: point.label.slice(5), value: Number(point.value) }));
}

function EmptyState({ text }: { text: string }): ReactElement {
  return <div className="flex min-h-[240px] items-center justify-center rounded-2xl border border-dashed text-sm text-muted-foreground">{text}</div>;
}

export function AnalyticsClient(): ReactElement {
  const [mode, setMode] = useState<RangeMode>("last_30_days");
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const [downloadingFormat, setDownloadingFormat] = useState<"csv" | "excel" | "pdf" | null>(null);

  const queryParams = useMemo(() => {
    if (mode === "custom" && customStart && customEnd) {
      return { startDate: customStart, endDate: customEnd };
    }
    return { preset: mode === "custom" ? "last_30_days" : mode };
  }, [customEnd, customStart, mode]);

  const revenueQuery = useQuery({
    queryKey: ["analytics-revenue", queryParams],
    queryFn: () => getRevenueAnalytics(queryParams),
  });
  const ordersQuery = useQuery({
    queryKey: ["analytics-orders", queryParams],
    queryFn: () => getOrdersAnalytics(queryParams),
  });
  const productsQuery = useQuery({
    queryKey: ["analytics-products", queryParams],
    queryFn: () => getProductsAnalytics(queryParams),
  });
  const customersQuery = useQuery({
    queryKey: ["analytics-customers", queryParams],
    queryFn: () => getCustomersAnalytics(queryParams),
  });

  const isLoading =
    revenueQuery.isLoading || ordersQuery.isLoading || productsQuery.isLoading || customersQuery.isLoading;
  const hasError =
    revenueQuery.isError || ordersQuery.isError || productsQuery.isError || customersQuery.isError;

  const revenueDaily = useMemo(
    () => (revenueQuery.data ? parseSeries(revenueQuery.data.daily) : []),
    [revenueQuery.data],
  );
  const revenueMonthly = useMemo(
    () => (revenueQuery.data ? parseSeries(revenueQuery.data.monthly) : []),
    [revenueQuery.data],
  );
  const ordersDaily = useMemo(
    () => (ordersQuery.data ? parseSeries(ordersQuery.data.daily) : []),
    [ordersQuery.data],
  );
  const ordersMonthly = useMemo(
    () => (ordersQuery.data ? parseSeries(ordersQuery.data.monthly) : []),
    [ordersQuery.data],
  );

  const activeParams = mode === "custom" ? { startDate: customStart, endDate: customEnd } : { preset: mode };

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-4">
        <div className="space-y-2">
          <SectionBadge>Аналитика</SectionBadge>
          <h1 className="text-3xl font-semibold tracking-tight">Аналитика бизнеса</h1>
          <p className="max-w-2xl text-sm text-muted-foreground">
            Анализируйте выручку, заказы, товары, клиентов и склад с фильтрами, удобными для командного анализа.
          </p>
        </div>
        <SegmentControl value={mode} options={analyticsRangeOptions} onChange={setMode} />
        {mode === "custom" ? (
          <Card>
            <CardContent className="grid gap-4 p-4 md:grid-cols-[1fr_1fr_auto]">
              <label className="grid gap-2 text-sm">
                <span className="text-muted-foreground">Start date</span>
                <input
                  type="date"
                  value={customStart}
                  onChange={(event) => setCustomStart(event.target.value)}
                  className="h-11 rounded-xl border bg-background px-3"
                />
              </label>
              <label className="grid gap-2 text-sm">
                <span className="text-muted-foreground">End date</span>
                <input
                  type="date"
                  value={customEnd}
                  onChange={(event) => setCustomEnd(event.target.value)}
                  className="h-11 rounded-xl border bg-background px-3"
                />
              </label>
              <div className="flex items-end">
                <Button type="button" variant="outline" onClick={() => setMode("last_30_days")}>
                  Сбросить диапазон
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : null}
        <div className="flex flex-wrap gap-3">
          <Button
            type="button"
            variant="outline"
            disabled={downloadingFormat !== null}
            onClick={async () => {
              setDownloadingFormat("csv");
              try {
                await downloadAnalyticsExport("csv", activeParams);
              } finally {
                setDownloadingFormat(null);
              }
            }}
          >
            <Download className="h-4 w-4" />
            {downloadingFormat === "csv" ? "Скачиваем..." : "CSV"}
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={downloadingFormat !== null}
            onClick={async () => {
              setDownloadingFormat("excel");
              try {
                await downloadAnalyticsExport("excel", activeParams);
              } finally {
                setDownloadingFormat(null);
              }
            }}
          >
            <FileSpreadsheet className="h-4 w-4" />
            {downloadingFormat === "excel" ? "Скачиваем..." : "Excel"}
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={downloadingFormat !== null}
            onClick={async () => {
              setDownloadingFormat("pdf");
              try {
                await downloadAnalyticsExport("pdf", activeParams);
              } finally {
                setDownloadingFormat(null);
              }
            }}
          >
            <FileText className="h-4 w-4" />
            {downloadingFormat === "pdf" ? "Скачиваем..." : "PDF"}
          </Button>
        </div>
      </section>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 8 }, (_, index) => (
            <Card key={index} className="h-28 animate-pulse bg-muted/40" />
          ))}
        </div>
      ) : hasError ? (
        <Card>
          <CardContent className="flex items-center gap-3 p-6 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            Аналитику не удалось загрузить. Попробуйте ещё раз.
          </CardContent>
        </Card>
      ) : revenueQuery.data && ordersQuery.data && productsQuery.data && customersQuery.data ? (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Выполненные заказы" value={formatCount(ordersQuery.data.status_breakdown.completed_orders)} />
            <MetricCard label="Отменённые заказы" value={formatCount(ordersQuery.data.status_breakdown.cancelled_orders)} />
            <MetricCard label="Черновики заказов" value={formatCount(ordersQuery.data.status_breakdown.draft_orders)} />
            <MetricCard label="Средний чек заказа" value={formatMoney(ordersQuery.data.status_breakdown.average_order_value)} />
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <Panel title="Выручка по дням" description="Выручка по завершённым заказам за выбранный период.">
              {revenueDaily.length > 0 ? (
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={revenueDaily}>
                      <defs>
                        <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0.02} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} />
                      <YAxis tickLine={false} axisLine={false} width={60} />
                      <Tooltip formatter={(value) => formatMoney(String(value))} />
                      <Area type="monotone" dataKey="value" stroke="hsl(var(--primary))" fill="url(#revenueGradient)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState text="За этот период выручки нет." />
              )}
            </Panel>

            <Panel title="Заказы по дням" description="Объём заказов за выбранный период.">
              {ordersDaily.length > 0 ? (
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={ordersDaily}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} />
                      <YAxis tickLine={false} axisLine={false} width={44} />
                      <Tooltip formatter={(value) => formatCount(Number(value))} />
                      <Bar dataKey="value" fill="hsl(var(--primary))" radius={[10, 10, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState text="За этот период заказов нет." />
              )}
            </Panel>
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <Panel title="Выручка по месяцам" description="Месячный тренд для более широкого обзора.">
              {revenueMonthly.length > 0 ? (
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={revenueMonthly}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} />
                      <YAxis tickLine={false} axisLine={false} width={60} />
                      <Tooltip formatter={(value) => formatMoney(String(value))} />
                      <Line type="monotone" dataKey="value" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState text="Здесь появится месячная выручка." />
              )}
            </Panel>

            <Panel title="Заказы по месяцам" description="Месячный объём заказов.">
              {ordersMonthly.length > 0 ? (
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={ordersMonthly}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} />
                      <YAxis tickLine={false} axisLine={false} width={44} />
                      <Tooltip formatter={(value) => formatCount(Number(value))} />
                      <Line type="monotone" dataKey="value" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <EmptyState text="Здесь появятся месячные заказы." />
              )}
            </Panel>
          </section>

          <section className="grid gap-6 xl:grid-cols-3">
            <Panel title="Топ товаров" description="Самые продаваемые позиции по выручке.">
              <div className="flex flex-col gap-3">
                {productsQuery.data.top_products.slice(0, 6).map((product) => (
                  <div key={`${product.product_name}-${product.sku ?? "sku"}`} className="flex items-center justify-between gap-4 rounded-2xl border p-4">
                    <div>
                      <p className="font-medium">{product.product_name}</p>
                      <p className="text-xs text-muted-foreground">{product.sku ?? "Без SKU"}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{formatMoney(product.revenue)}</p>
                      <p className="text-xs text-muted-foreground">{formatCount(Number(product.quantity_sold))} продано</p>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel title="Топ категорий" description="Выручка по категориям товаров.">
              <div className="flex flex-col gap-3">
                {productsQuery.data.top_categories.slice(0, 6).map((category) => (
                  <div key={category.category_name} className="flex items-center justify-between gap-4 rounded-2xl border p-4">
                    <div>
                      <p className="font-medium">{category.category_name}</p>
                      <p className="text-xs text-muted-foreground">{formatCount(category.product_count)} товаров</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{formatMoney(category.revenue)}</p>
                      <p className="text-xs text-muted-foreground">{formatCount(Number(category.quantity_sold))} продано</p>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel title="Сводка склада" description="Текущее состояние склада.">
              <div className="grid gap-3">
                <Card className="border-dashed">
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-2">
                      <Layers3 className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">Стоимость склада</span>
                    </div>
                    <span className="font-medium">{formatMoney(productsQuery.data.inventory_summary.inventory_value)}</span>
                  </CardContent>
                </Card>
                <Card className="border-dashed">
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-2">
                      <PackageSearch className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">Низкий запас</span>
                    </div>
                    <span className="font-medium">{formatCount(productsQuery.data.inventory_summary.low_stock_products)}</span>
                  </CardContent>
                </Card>
                <Card className="border-dashed">
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">Нет в наличии</span>
                    </div>
                    <span className="font-medium">{formatCount(productsQuery.data.inventory_summary.out_of_stock_products)}</span>
                  </CardContent>
                </Card>
              </div>
            </Panel>
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <Panel title="Топ клиентов" description="Клиенты по выручке от завершённых заказов.">
              <div className="flex flex-col gap-3">
                {customersQuery.data.top_customers.slice(0, 8).map((customer) => (
                  <div key={`${customer.customer_name}-${customer.customer_phone ?? "phone"}`} className="flex items-center justify-between gap-4 rounded-2xl border p-4">
                    <div>
                      <p className="font-medium">{customer.customer_name}</p>
                      <p className="text-xs text-muted-foreground">{customer.customer_phone ?? "Без телефона"}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{formatMoney(customer.revenue)}</p>
                      <p className="text-xs text-muted-foreground">{formatCount(customer.order_count)} заказов</p>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel title="Последние заказы" description="Последняя активность за выбранный период.">
              <div className="flex flex-col gap-3">
                {ordersQuery.data.recent_orders.slice(0, 8).map((order) => (
                  <div key={order.id} className="flex items-center justify-between gap-4 rounded-2xl border p-4">
                    <div>
                      <p className="font-medium">{order.customer_name ?? "Anonymous customer"}</p>
                      <p className="text-xs text-muted-foreground">{order.invoice_number}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{formatMoney(order.total)}</p>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">{order.status}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>
          </section>
        </>
      ) : null}
    </div>
  );
}
