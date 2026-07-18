"use client";

import { Download, FileSpreadsheet, FileText, Receipt, ShieldCheck } from "lucide-react";
import { useMemo, useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { downloadAnalyticsExport, getDashboardAnalytics } from "@/lib/analytics";
import { analyticsPresets, formatCount, formatMoney, MetricCard, Panel, SectionBadge, SegmentControl } from "@/components/analytics/shared";
import type { AnalyticsPreset } from "@/types/analytics";

type RangeMode = AnalyticsPreset | "custom";
const reportRangeOptions = [...analyticsPresets, { value: "custom", label: "Custom range" }] as const;

export function ReportsClient(): ReactElement {
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

  const dashboardQuery = useQuery({
    queryKey: ["reports-dashboard", queryParams],
    queryFn: () => getDashboardAnalytics(queryParams),
  });

  const activeParams = mode === "custom" ? { startDate: customStart, endDate: customEnd } : { preset: mode };

  return (
    <div className="flex flex-col gap-6">
      <section className="space-y-2">
        <SectionBadge>Reports</SectionBadge>
        <h1 className="text-3xl font-semibold tracking-tight">Reports and exports</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Export operational analytics for finance, inventory, and leadership reviews.
        </p>
      </section>

      <SegmentControl value={mode} options={reportRangeOptions} onChange={setMode} />

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
                Reset range
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
          {downloadingFormat === "csv" ? "Downloading..." : "CSV export"}
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
          {downloadingFormat === "excel" ? "Downloading..." : "Excel export"}
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
          {downloadingFormat === "pdf" ? "Downloading..." : "PDF export"}
        </Button>
      </div>

      {dashboardQuery.data ? (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Today revenue" value={formatMoney(dashboardQuery.data.metrics.today_revenue)} />
            <MetricCard label="This month revenue" value={formatMoney(dashboardQuery.data.metrics.month_revenue)} />
            <MetricCard label="Total products" value={formatCount(dashboardQuery.data.metrics.total_products)} />
            <MetricCard label="Inventory value" value={formatMoney(dashboardQuery.data.inventory_summary.inventory_value)} />
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <Panel title="Export checklist" description="These downloads cover the main operational reporting needs.">
              <div className="grid gap-3">
                <div className="flex items-center justify-between rounded-2xl border p-4">
                  <div className="flex items-center gap-3">
                    <Receipt className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">Financial snapshot</span>
                  </div>
                  <span className="text-sm text-muted-foreground">{formatMoney(dashboardQuery.data.metrics.month_revenue)}</span>
                </div>
                <div className="flex items-center justify-between rounded-2xl border p-4">
                  <div className="flex items-center gap-3">
                    <ShieldCheck className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">Stock risk</span>
                  </div>
                  <span className="text-sm text-muted-foreground">{formatCount(dashboardQuery.data.inventory_summary.low_stock_products)} low stock</span>
                </div>
              </div>
            </Panel>

            <Panel title="Recent orders" description="Orders included in the current reporting scope.">
              <div className="flex flex-col gap-3">
                {dashboardQuery.data.recent_orders.slice(0, 6).map((order) => (
                  <div key={order.id} className="flex items-center justify-between rounded-2xl border p-4">
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
