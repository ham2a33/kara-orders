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
        <SectionBadge>Биллинг</SectionBadge>
        <h1 className="text-3xl font-semibold tracking-tight">Архитектура биллинга</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Платёжные шлюзы в этой стадии намеренно исключены. Мы управляем только внутренним состоянием биллинга и метаданными подписки.
        </p>
      </section>

      {billing ? (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Тариф" value={billing.plan.name} />
          <MetricCard label="Цена в месяц" value={formatMoney(billing.plan.price_monthly, billing.plan.currency)} />
          <MetricCard label="Setup fee" value={formatMoney(billing.setup_fee_amount, billing.plan.currency)} />
          <MetricCard label="Статус" value={billing.status} />
        </section>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <CreditCard className="mt-0.5 h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Биллинг отключён</p>
              <p className="text-sm text-muted-foreground">{billing?.billing_disabled ? "Да" : "Нет"}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <ReceiptText className="mt-0.5 h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Статус Setup fee</p>
              <p className="text-sm text-muted-foreground">
                {billing?.setup_fee_paid ? `Оплачено ${formatDate(billing.setup_fee_paid_at)}` : "Не оплачено"}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <BadgeDollarSign className="mt-0.5 h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Период подписки</p>
              <p className="text-sm text-muted-foreground">
                {subscription ? `${formatDate(subscription.subscription_start)} → ${formatDate(subscription.subscription_end)}` : "Нет данных"}
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <Panel title="Метаданные биллинга" description="Архитектура оставляет место для будущих платёжных интеграций.">
        <div className="grid gap-4 md:grid-cols-2">
          {[
            ["Текущий тариф", billing?.plan.slug ?? "—"],
            ["Окончание trial", formatDate(subscription?.trial_end ?? null)],
            ["Старт подписки", formatDate(subscription?.subscription_start ?? null)],
            ["Окончание подписки", formatDate(subscription?.subscription_end ?? null)],
            ["Сумма setup fee", billing ? formatMoney(billing.setup_fee_amount, billing.plan.currency) : "—"],
            ["Период", billing?.plan.billing_cycle ?? "—"],
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
          <span>Всё поведение биллинга основано на внутренних данных подписки, лимитах тарифа и аудит-логах.</span>
          <Pill tone="secondary">Готово к платёжному провайдеру</Pill>
        </CardContent>
      </Card>
    </div>
  );
}
