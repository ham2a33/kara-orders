"use client";

import { CreditCard, ReceiptText, BadgeDollarSign, ShieldCheck } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { MetricCard, Panel, Pill, SectionBadge, formatDate, formatMoney } from "@/components/platform/shared";
import { getBilling, getSubscriptionOverview } from "@/lib/platform";

export default function BillingPage(): ReactElement {
  const billingQuery = useQuery({
    queryKey: ["platform-billing"],
    queryFn: getBilling,
  });
  const subscriptionQuery = useQuery({
    queryKey: ["platform-billing-overview"],
    queryFn: getSubscriptionOverview,
  });

  const billing = billingQuery.data;
  const subscription = subscriptionQuery.data?.subscription;

  return (
    <div className="flex flex-col gap-6">
      <section className="space-y-2">
        <SectionBadge>Billing</SectionBadge>
        <h1 className="text-3xl font-semibold tracking-tight">Billing architecture</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Payment gateways are intentionally excluded in this stage. We only manage the internal billing state and future-proof subscription metadata.
        </p>
      </section>

      {billing ? (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Plan" value={billing.plan.name} />
          <MetricCard label="Monthly price" value={formatMoney(billing.plan.price_monthly, billing.plan.currency)} />
          <MetricCard label="Setup fee" value={formatMoney(billing.setup_fee_amount, billing.plan.currency)} />
          <MetricCard label="Status" value={billing.status} />
        </section>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <CreditCard className="mt-0.5 h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Billing disabled</p>
              <p className="text-sm text-muted-foreground">{billing?.billing_disabled ? "Yes" : "No"}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <ReceiptText className="mt-0.5 h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Setup fee status</p>
              <p className="text-sm text-muted-foreground">
                {billing?.setup_fee_paid ? `Paid ${formatDate(billing.setup_fee_paid_at)}` : "Not paid"}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <BadgeDollarSign className="mt-0.5 h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Subscription window</p>
              <p className="text-sm text-muted-foreground">
                {subscription ? `${formatDate(subscription.subscription_start)} → ${formatDate(subscription.subscription_end)}` : "No data"}
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <Panel title="Billing metadata" description="The architecture leaves room for future payment provider integrations.">
        <div className="grid gap-4 md:grid-cols-2">
          {[
            ["Current plan", billing?.plan.slug ?? "—"],
            ["Trial end", formatDate(subscription?.trial_end ?? null)],
            ["Subscription start", formatDate(subscription?.subscription_start ?? null)],
            ["Subscription end", formatDate(subscription?.subscription_end ?? null)],
            ["Setup fee amount", billing ? formatMoney(billing.setup_fee_amount, billing.plan.currency) : "—"],
            ["Billing cycle", billing?.plan.billing_cycle ?? "—"],
          ].map(([label, value]) => (
            <div key={label} className="rounded-2xl border bg-muted/30 p-4">
              <p className="text-sm text-muted-foreground">{label}</p>
              <p className="mt-1 text-sm font-medium">{value}</p>
            </div>
          ))}
        </div>
      </Panel>

      <Card>
        <CardContent className="flex flex-wrap items-center gap-2 p-5 text-sm text-muted-foreground">
          <ShieldCheck className="h-4 w-4" />
          <span>All billing behavior is driven by internal subscription records, plan limits, and audit logs.</span>
          <Pill tone="secondary">Payment provider ready</Pill>
        </CardContent>
      </Card>
    </div>
  );
}
