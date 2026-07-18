"use client";

import { Database, Gauge, HardDrive } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { MetricCard, Panel, SectionBadge, formatCount, formatDate, formatMoney, formatBytes } from "@/components/platform/shared";
import { getSubscriptionOverview, getUsage } from "@/lib/platform";

export default function UsagePage(): ReactElement {
  const usageQuery = useQuery({
    queryKey: ["platform-usage"],
    queryFn: getUsage,
  });
  const subscriptionQuery = useQuery({
    queryKey: ["platform-usage-subscription"],
    queryFn: getSubscriptionOverview,
  });

  const usage = usageQuery.data;
  const subscription = subscriptionQuery.data?.subscription;

  return (
    <div className="flex flex-col gap-6">
      <section className="space-y-2">
        <SectionBadge>Usage</SectionBadge>
        <h1 className="text-3xl font-semibold tracking-tight">Monthly usage tracking</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Monitor AI requests, token usage, storage consumption, and recognition speed in one place.
        </p>
      </section>

      {usage ? (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="AI requests" value={formatCount(usage.monthly_ai_requests)} />
          <MetricCard label="Token usage" value={formatCount(usage.monthly_token_usage)} />
          <MetricCard label="Recognition count" value={formatCount(usage.recognition_count)} />
          <MetricCard label="Storage usage" value={formatBytes(usage.storage_usage_bytes)} />
        </section>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <Gauge className="mt-0.5 h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Average recognition time</p>
              <p className="text-sm text-muted-foreground">
                {usage ? `${usage.average_recognition_time_ms} ms` : "No data yet"}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <Database className="mt-0.5 h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Estimated AI cost</p>
              <p className="text-sm text-muted-foreground">
                {usage ? formatMoney(usage.estimated_ai_cost, subscription?.plan.currency ?? "KZT") : "No data yet"}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <HardDrive className="mt-0.5 h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Period window</p>
              <p className="text-sm text-muted-foreground">
                {usage ? `${formatDate(usage.period_start)} → ${formatDate(usage.period_end)}` : "No usage window"}
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <Panel title="Usage breakdown" description="Backend-managed counters reset on monthly boundaries.">
        <div className="grid gap-4 md:grid-cols-2">
          {[
            ["Monthly AI requests", usage?.monthly_ai_requests],
            ["Monthly tokens", usage?.monthly_token_usage],
            ["Recognition count", usage?.recognition_count],
            ["Storage usage", usage ? formatBytes(usage.storage_usage_bytes) : "—"],
          ].map(([label, value]) => (
            <div key={label} className="rounded-2xl border bg-muted/30 p-4">
              <p className="text-sm text-muted-foreground">{label}</p>
              <p className="mt-1 text-lg font-semibold">{value === undefined ? "—" : String(value)}</p>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Limit strategy" description="Usage is enforced against the plan attached to the company subscription.">
        <div className="grid gap-3 md:grid-cols-3">
          {[
            "AI requests are checked before every recognition request.",
            "Storage usage is updated after uploads and AI media processing.",
            "Orders and product counts are validated before create operations.",
          ].map((item) => (
            <div key={item} className="rounded-2xl border bg-card p-4 text-sm text-muted-foreground">
              {item}
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
