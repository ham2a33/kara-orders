"use client";

import type { ReactElement, ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export const analyticsPresets = [
  { value: "today", label: "Сегодня" },
  { value: "yesterday", label: "Вчера" },
  { value: "last_7_days", label: "7 дней" },
  { value: "last_30_days", label: "30 дней" },
  { value: "this_month", label: "Этот месяц" },
  { value: "last_month", label: "Прошлый месяц" },
] as const;

export function formatMoney(value: string): string {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return value;
  }
  return numeric.toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function formatCount(value: number): string {
  return new Intl.NumberFormat("ru-RU").format(value);
}

export function SectionBadge({ children }: { children: ReactNode }): ReactElement {
  return <Badge className="w-fit rounded-full px-3 py-1 text-xs">{children}</Badge>;
}

export function MetricCard({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description?: string;
}): ReactElement {
  return (
    <Card>
      <CardHeader className="space-y-1">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl tracking-tight">{value}</CardTitle>
        {description ? <p className="text-xs text-muted-foreground">{description}</p> : null}
      </CardHeader>
    </Card>
  );
}

export function Panel({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}): ReactElement {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="space-y-1 border-b bg-muted/20">
        <CardTitle className="text-base">{title}</CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      <CardContent className="p-6">{children}</CardContent>
    </Card>
  );
}

export function SegmentControl<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: readonly { value: T; label: string }[];
  onChange: (value: T) => void;
}): ReactElement {
  return (
    <div className="flex flex-wrap gap-2 rounded-2xl border bg-card p-2">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          className={cn(
            "rounded-xl px-4 py-2 text-sm font-medium transition-colors",
            value === option.value ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
