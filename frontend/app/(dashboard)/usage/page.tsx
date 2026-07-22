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
        <SectionBadge>Использование</SectionBadge>
        <h1 className="text-3xl font-semibold tracking-tight">Ежемесячный трекинг использования</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Отслеживайте AI-запросы, токены, хранилище и скорость распознавания в одном месте.
        </p>
      </section>

      {usage ? (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="AI-запросы" value={formatCount(usage.monthly_ai_requests)} />
          <MetricCard label="Использование токенов" value={formatCount(usage.monthly_token_usage)} />
          <MetricCard label="Количество распознаваний" value={formatCount(usage.recognition_count)} />
          <MetricCard label="Использование хранилища" value={formatBytes(usage.storage_usage_bytes)} />
        </section>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <Gauge className="mt-0.5 h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Среднее время распознавания</p>
              <p className="text-sm text-muted-foreground">
                {usage ? `${usage.average_recognition_time_ms} мс` : "Пока нет данных"}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <Database className="mt-0.5 h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Оценочная стоимость AI</p>
              <p className="text-sm text-muted-foreground">
                {usage ? formatMoney(usage.estimated_ai_cost, subscription?.plan.currency ?? "KZT") : "Пока нет данных"}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-start gap-3 p-5">
            <HardDrive className="mt-0.5 h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Период</p>
              <p className="text-sm text-muted-foreground">
                {usage ? `${formatDate(usage.period_start)} → ${formatDate(usage.period_end)}` : "Нет периода"}
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <Panel title="Разбивка использования" description="Счётчики управляются backend и сбрасываются ежемесячно.">
        <div className="grid gap-4 md:grid-cols-2">
          {[
            ["AI-запросы за месяц", usage?.monthly_ai_requests],
            ["Токены за месяц", usage?.monthly_token_usage],
            ["Распознавания", usage?.recognition_count],
            ["Хранилище", usage ? formatBytes(usage.storage_usage_bytes) : "—"],
          ].map(([label, value]) => (
            <div key={label} className="rounded-2xl border bg-muted/30 p-4">
              <p className="text-sm text-muted-foreground">{label}</p>
              <p className="mt-1 text-lg font-semibold">{value === undefined ? "—" : String(value)}</p>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Логика лимитов" description="Использование проверяется относительно тарифа компании.">
        <div className="grid gap-3 md:grid-cols-3">
          {[
            "AI-запросы проверяются перед каждым распознаванием.",
            "Использование хранилища обновляется после загрузок и обработки медиа.",
            "Количество заказов и товаров проверяется до операций создания.",
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
