"use client";

import { Check, Crown, ShieldAlert } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import type { ReactElement } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { MetricCard, Panel, Pill, SectionBadge, formatCount, formatDate, formatMoney } from "@/components/platform/shared";
import { getPlans, getSubscriptionOverview } from "@/lib/platform";

function limitValue(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "Без лимита";
  }
  return formatCount(value);
}

export default function SubscriptionPage(): ReactElement {
  const subscriptionQuery = useQuery({
    queryKey: ["platform-subscription"],
    queryFn: getSubscriptionOverview,
  });
  const plansQuery = useQuery({
    queryKey: ["platform-plans"],
    queryFn: getPlans,
  });

  const subscription = subscriptionQuery.data?.subscription;
  const limits = subscriptionQuery.data?.limits;

  return (
    <div className="flex flex-col gap-6">
      <section className="space-y-2">
        <SectionBadge>Подписка</SectionBadge>
        <h1 className="text-3xl font-semibold tracking-tight">Тариф и использование</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Отслеживайте активный тариф, пробный период и лимиты текущей компании.
        </p>
      </section>

      {subscription ? (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Текущий тариф" value={subscription.plan.name} description={subscription.plan.slug} />
          <MetricCard label="Цена тарифа" value={formatMoney(subscription.plan.price_monthly, subscription.plan.currency)} />
          <MetricCard label="AI-запросы" value={formatCount(subscription.ai_requests_monthly)} description="За текущий период" />
          <MetricCard label="Использование хранилища" value={formatCount(subscription.storage_usage_bytes)} description="Отслеживаемые байты" />
        </section>
      ) : null}

      {subscription && limits ? (
        <Panel title="Детали подписки" description="Лимиты проверяются на backend и синхронизируются ежемесячно.">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {[
              ["Статус", subscription.status],
              ["Пробный период до", formatDate(subscription.trial_end)],
              ["Биллинг отключён", subscription.billing_disabled ? "Да" : "Нет"],
              ["Старт подписки", formatDate(subscription.subscription_start)],
              ["Окончание подписки", formatDate(subscription.subscription_end)],
              ["Setup fee оплачена", subscription.setup_fee_paid ? "Да" : "Нет"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl border bg-muted/30 p-4">
                <p className="text-sm text-muted-foreground">{label}</p>
                <p className="mt-1 text-sm font-medium">{value}</p>
              </div>
            ))}
          </div>
        </Panel>
      ) : null}

      {limits ? (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <MetricCard label="Макс. пользователей" value={limitValue(limits.maximum_users)} />
          <MetricCard label="Макс. товаров" value={limitValue(limits.maximum_products)} />
          <MetricCard label="Макс. AI-запросов" value={limitValue(limits.maximum_ai_requests)} />
          <MetricCard label="Макс. хранилище" value={limitValue(limits.maximum_storage_bytes)} />
          <MetricCard label="Макс. компаний" value={limitValue(limits.maximum_companies)} />
          <MetricCard label="Макс. заказов в месяц" value={limitValue(limits.maximum_orders_per_month)} />
        </section>
      ) : null}

      <Panel title="Доступные тарифы" description="Тариф Business — тариф по умолчанию для production.">
        {plansQuery.data ? (
          <div className="grid gap-4 xl:grid-cols-2">
            {plansQuery.data.items.map((plan) => (
              <Card key={plan.id} className="border-muted">
                <CardContent className="flex h-full flex-col gap-4 p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-lg font-semibold">{plan.name}</h3>
                        {plan.is_default ? <Pill tone="success">По умолчанию</Pill> : null}
                        {plan.slug === "business" ? <Pill tone="warning">Рекомендуем</Pill> : null}
                      </div>
                      <p className="text-sm text-muted-foreground">{plan.description}</p>
                    </div>
                    <Crown className="h-5 w-5 text-muted-foreground" />
                  </div>

                  <div className="grid gap-3 text-sm md:grid-cols-2">
                    <div className="rounded-2xl border bg-muted/20 p-4">
                      <p className="text-muted-foreground">Цена в месяц</p>
                      <p className="mt-1 font-medium">{formatMoney(plan.price_monthly, plan.currency)}</p>
                    </div>
                    <div className="rounded-2xl border bg-muted/20 p-4">
                      <p className="text-muted-foreground">Период биллинга</p>
                      <p className="mt-1 font-medium">{plan.billing_cycle}</p>
                    </div>
                  </div>

                  <div className="grid gap-2 text-sm text-muted-foreground md:grid-cols-2">
                    {Object.entries(plan.limits).slice(0, 4).map(([label, value]) => (
                      <div key={label} className="flex items-center justify-between rounded-2xl border px-4 py-3">
                        <span>{label}</span>
                        <span className="font-medium text-foreground">{value === null ? "Без лимита" : String(value)}</span>
                      </div>
                    ))}
                  </div>

                  <div className="flex flex-wrap items-center gap-2 text-sm">
                    {Boolean(plan.features.analytics) ? <Pill tone="secondary">Аналитика</Pill> : null}
                    {Boolean(plan.features.pdf_invoices) ? <Pill tone="secondary">PDF-счета</Pill> : null}
                    {Boolean(plan.features.ai_recognition) ? <Pill tone="secondary">AI</Pill> : null}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 3 }, (_, index) => (
              <Card key={index} className="h-44 animate-pulse bg-muted/30" />
            ))}
          </div>
        )}
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <Check className="mt-0.5 h-5 w-5 text-emerald-500" />
            <div>
            <p className="font-medium">Лимиты проверяются на backend</p>
            <p className="text-sm text-muted-foreground">
                Слой подписки проверяет каждый лимит на сервере до того, как будут приняты операции с товарами, заказами, AI или хранилищем.
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <ShieldAlert className="mt-0.5 h-5 w-5 text-amber-500" />
            <div>
            <p className="font-medium">Пробный период и статусы</p>
            <p className="text-sm text-muted-foreground">
                Компании могут переходить между trial, active, past due, suspended, expired, lifetime и custom без изменения платёжной архитектуры.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
