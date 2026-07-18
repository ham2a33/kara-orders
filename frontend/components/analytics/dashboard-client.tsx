"use client";

import { AlertCircle, ArrowUpRight, Package, ReceiptText, TrendingUp } from "lucide-react";
import { useMemo, useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  BarChart,
  Bar,
} from "recharts";

import { Card, CardContent } from "@/components/ui/card";
import { getDashboardAnalytics } from "@/lib/analytics";
import { analyticsPresets, formatCount, formatMoney, MetricCard, Panel, SectionBadge, SegmentControl } from "@/components/analytics/shared";
import type { AnalyticsSeriesPoint, DashboardResponse } from "@/types/analytics";

function toChartData(points: AnalyticsSeriesPoint[]): Array<{ label: string; value: number }> {
  return points.map((point) => ({ label: point.label.slice(5), value: Number(point.value) }));
}

function emptyMessage(text: string): ReactElement {
  return <div className="flex min-h-[240px] items-center justify-center rounded-2xl border border-dashed text-sm text-muted-foreground">{text}</div>;
}

export function DashboardClient(): ReactElement {
  const [preset, setPreset] = useState<DashboardResponse["range"]["preset"]>("last_30_days");
  const dashboardQuery = useQuery({
    queryKey: ["dashboard", preset],
    queryFn: () => getDashboardAnalytics({ preset }),
  });

  const data = dashboardQuery.data;
  const revenueData = useMemo(() => (data ? toChartData(data.revenue_by_day) : []), [data]);
  const ordersData = useMemo(() => (data ? toChartData(data.orders_by_day) : []), [data]);

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-4">
        <div className="flex items-center justify-between gap-4">
          <div className="space-y-2">
            <SectionBadge>Dashboard</SectionBadge>
            <h1 className="text-3xl font-semibold tracking-tight">Business overview</h1>
            <p className="max-w-2xl text-sm text-muted-foreground">
              A fast snapshot of revenue, orders, products, and inventory across your company.
            </p>
          </div>
          <ArrowUpRight className="hidden h-5 w-5 text-muted-foreground md:block" />
        </div>
        <SegmentControl value={preset} options={analyticsPresets} onChange={setPreset} />
      </section>

      {dashboardQuery.isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 10 }, (_, index) => (
            <Card key={index} className="h-28 animate-pulse bg-muted/40" />
          ))}
        </div>
      ) : dashboardQuery.isError ? (
        <Card>
          <CardContent className="flex items-center gap-3 p-6 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            Could not load dashboard data. Please try again.
          </CardContent>
        </Card>
      ) : data ? (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Today revenue" value={formatMoney(data.metrics.today_revenue)} />
            <MetricCard label="This week revenue" value={formatMoney(data.metrics.week_revenue)} />
            <MetricCard label="This month revenue" value={formatMoney(data.metrics.month_revenue)} />
            <MetricCard label="Average invoice" value={formatMoney(data.metrics.average_invoice)} />
            <MetricCard label="Today orders" value={formatCount(data.metrics.today_orders)} />
            <MetricCard label="This week orders" value={formatCount(data.metrics.week_orders)} />
            <MetricCard label="This month orders" value={formatCount(data.metrics.month_orders)} />
            <MetricCard label="Total products" value={formatCount(data.metrics.total_products)} />
            <MetricCard label="Low stock products" value={formatCount(data.metrics.low_stock_products)} />
            <MetricCard label="Out of stock products" value={formatCount(data.metrics.out_of_stock_products)} />
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <Panel title="Revenue by day" description="Completed order revenue within the selected period.">
              {revenueData.length > 0 ? (
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={revenueData} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="dashboardRevenue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0.02} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} />
                      <YAxis tickLine={false} axisLine={false} width={56} />
                      <Tooltip formatter={(value) => formatMoney(String(value))} />
                      <Area type="monotone" dataKey="value" stroke="hsl(var(--primary))" fill="url(#dashboardRevenue)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                emptyMessage("No revenue in this period yet.")
              )}
            </Panel>

            <Panel title="Orders by day" description="All order statuses in the selected period.">
              {ordersData.length > 0 ? (
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={ordersData} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} />
                      <YAxis tickLine={false} axisLine={false} width={40} />
                      <Tooltip formatter={(value) => formatCount(Number(value))} />
                      <Bar dataKey="value" fill="hsl(var(--primary))" radius={[10, 10, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                emptyMessage("No orders in this period yet.")
              )}
            </Panel>
          </section>

          <section className="grid gap-6 xl:grid-cols-3">
            <Panel title="Top products" description="Most sold products by completed order volume.">
              <div className="flex flex-col gap-3">
                {data.top_products.slice(0, 5).map((product) => (
                  <div key={`${product.product_name}-${product.sku ?? "sku"}`} className="flex items-center justify-between gap-4 rounded-2xl border p-4">
                    <div>
                      <p className="font-medium">{product.product_name}</p>
                      <p className="text-xs text-muted-foreground">{product.sku ?? "No SKU"}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{formatCount(Number(product.quantity_sold))} sold</p>
                      <p className="text-xs text-muted-foreground">{formatMoney(product.revenue)} revenue</p>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel title="Top categories" description="Category performance for the selected period.">
              <div className="flex flex-col gap-3">
                {data.top_categories.slice(0, 5).map((category) => (
                  <div key={category.category_name} className="flex items-center justify-between gap-4 rounded-2xl border p-4">
                    <div>
                      <p className="font-medium">{category.category_name}</p>
                      <p className="text-xs text-muted-foreground">{formatCount(category.product_count)} products</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{formatCount(Number(category.quantity_sold))} sold</p>
                      <p className="text-xs text-muted-foreground">{formatMoney(category.revenue)} revenue</p>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel title="Inventory summary" description="Live stock health across your catalog.">
              <div className="grid gap-3">
                <Card className="border-dashed">
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <Package className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">Inventory value</span>
                    </div>
                    <span className="font-medium">{formatMoney(data.inventory_summary.inventory_value)}</span>
                  </CardContent>
                </Card>
                <Card className="border-dashed">
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <TrendingUp className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">Low stock</span>
                    </div>
                    <span className="font-medium">{formatCount(data.inventory_summary.low_stock_products)}</span>
                  </CardContent>
                </Card>
                <Card className="border-dashed">
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <ReceiptText className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">Out of stock</span>
                    </div>
                    <span className="font-medium">{formatCount(data.inventory_summary.out_of_stock_products)}</span>
                  </CardContent>
                </Card>
              </div>
            </Panel>
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <Panel title="Recent orders" description="Latest orders across the selected period.">
              <div className="flex flex-col gap-3">
                {data.recent_orders.slice(0, 8).map((order) => (
                  <div key={order.id} className="flex items-center justify-between gap-4 rounded-2xl border p-4">
                    <div>
                      <p className="font-medium">{order.customer_name ?? "Anonymous customer"}</p>
                      <p className="text-xs text-muted-foreground">
                        {order.invoice_number} • {new Date(order.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{formatMoney(order.total)}</p>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">{order.status}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel title="Top customers" description="Customers contributing the most revenue.">
              <div className="flex flex-col gap-3">
                {data.top_customers.slice(0, 8).map((customer) => (
                  <div key={`${customer.customer_name}-${customer.customer_phone ?? "phone"}`} className="flex items-center justify-between gap-4 rounded-2xl border p-4">
                    <div>
                      <p className="font-medium">{customer.customer_name}</p>
                      <p className="text-xs text-muted-foreground">{customer.customer_phone ?? "No phone"}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{formatMoney(customer.revenue)}</p>
                      <p className="text-xs text-muted-foreground">{formatCount(customer.order_count)} orders</p>
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
