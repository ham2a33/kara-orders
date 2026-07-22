"use client";

import { useMemo, useState, type ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Crown, PauseCircle, PlayCircle, ShieldAlert, ToggleLeft, ToggleRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Panel, SectionBadge, formatCount, formatDate, formatMoney } from "@/components/platform/shared";
import {
  changeCompanyPlan,
  changeCompanyStatus,
  getAdminCompanies,
  getPlans,
  setCompanyBillingDisabled,
} from "@/lib/platform";

export default function AdminPage(): ReactElement {
  const queryClient = useQueryClient();
  const companiesQuery = useQuery({ queryKey: ["platform-admin-companies"], queryFn: getAdminCompanies });
  const plansQuery = useQuery({ queryKey: ["platform-admin-plans"], queryFn: getPlans });
  const [selectedPlanByCompany, setSelectedPlanByCompany] = useState<Record<string, string>>({});

  const planOptions = useMemo(() => plansQuery.data?.items ?? [], [plansQuery.data?.items]);
  const defaultPlanSlug = planOptions.find((plan) => plan.is_default)?.slug ?? planOptions[0]?.slug ?? "business";
  const companyStatusVariant = (status: string): "default" | "outline" | "success" | "warning" | "danger" => {
    if (status === "active") {
      return "success";
    }
    if (status === "suspended" || status === "expired" || status === "canceled") {
      return "danger";
    }
    return "warning";
  };

  const planMutation = useMutation({
    mutationFn: ({ companyId, planSlug }: { companyId: string; planSlug: string }) => changeCompanyPlan(companyId, planSlug),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["platform-admin-companies"] });
      await queryClient.invalidateQueries({ queryKey: ["platform-subscription"] });
      await queryClient.invalidateQueries({ queryKey: ["platform-billing"] });
    },
  });
  const statusMutation = useMutation({
    mutationFn: ({ companyId, status }: { companyId: string; status: "active" | "suspended" }) =>
      changeCompanyStatus(companyId, status),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["platform-admin-companies"] });
    },
  });
  const billingMutation = useMutation({
    mutationFn: ({ companyId, disabled }: { companyId: string; disabled: boolean }) =>
      setCompanyBillingDisabled(companyId, disabled),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["platform-admin-companies"] });
    },
  });

  const companies = companiesQuery.data?.items ?? [];

  const planNames = useMemo(() => {
    const map = new Map<string, string>();
    for (const plan of planOptions) {
      map.set(plan.name, plan.slug);
    }
    return map;
  }, [planOptions]);

  return (
    <div className="flex flex-col gap-6">
      <section className="space-y-2">
        <SectionBadge>Админ</SectionBadge>
        <h1 className="text-3xl font-semibold tracking-tight">Консоль супер-администратора</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Просматривайте компании, управляйте тарифами, приостанавливайте доступ и контролируйте биллинг без платёжных провайдеров.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-muted-foreground">Компании</p>
              <p className="mt-1 text-2xl font-semibold">{formatCount(companiesQuery.data?.total ?? 0)}</p>
            </div>
            <Crown className="h-5 w-5 text-muted-foreground" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-muted-foreground">Активные тарифы</p>
              <p className="mt-1 text-2xl font-semibold">{formatCount(planOptions.length)}</p>
            </div>
            <ShieldAlert className="h-5 w-5 text-muted-foreground" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-muted-foreground">Тариф Business</p>
              <p className="mt-1 text-2xl font-semibold">
                {formatMoney(planOptions.find((plan) => plan.slug === "business")?.price_monthly ?? "0")}
              </p>
            </div>
            <Badge>По умолчанию</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-sm text-muted-foreground">Действия с компаниями</p>
              <p className="mt-1 text-2xl font-semibold">В реальном времени</p>
            </div>
            <ToggleRight className="h-5 w-5 text-muted-foreground" />
          </CardContent>
        </Card>
      </section>

      <Panel title="Управление компаниями" description="Используйте серверные действия, чтобы синхронизировать тарифы и флаги биллинга.">
        <div className="grid gap-4">
          {companies.map((company) => {
            const selectedPlan = selectedPlanByCompany[company.id] ?? planNames.get(company.plan_name) ?? defaultPlanSlug;
            return (
              <Card key={company.id} className="border-muted">
                <CardContent className="grid gap-4 p-5 xl:grid-cols-[1.2fr_0.8fr_auto] xl:items-center">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-lg font-semibold">{company.name}</h3>
                      <Badge variant={companyStatusVariant(company.status)}>{company.status}</Badge>
                      {company.billing_disabled ? <Badge variant="danger">Биллинг отключён</Badge> : <Badge variant="outline">Биллинг включён</Badge>}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {company.email ?? "No company email"} • {company.plan_name} • AI requests {formatCount(company.ai_requests_monthly)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Created {formatDate(company.created_at)} • Setup fee {company.setup_fee_paid ? "paid" : "pending"}
                    </p>
                  </div>

                  <div className="grid gap-3">
                    <label className="grid gap-2 text-sm">
                        <span className="text-muted-foreground">Тариф</span>
                      <select
                        value={selectedPlan}
                        onChange={(event) =>
                          setSelectedPlanByCompany((current) => ({ ...current, [company.id]: event.target.value }))
                        }
                        className="h-11 rounded-xl border bg-background px-3"
                      >
                        {planOptions.map((plan) => (
                          <option key={plan.id} value={plan.slug}>
                            {plan.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        disabled={planMutation.isPending}
                        onClick={() => planMutation.mutate({ companyId: company.id, planSlug: selectedPlan })}
                      >
                        Изменить тариф
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        disabled={billingMutation.isPending}
                        onClick={() => billingMutation.mutate({ companyId: company.id, disabled: !company.billing_disabled })}
                      >
                        {company.billing_disabled ? <ToggleRight className="h-4 w-4" /> : <ToggleLeft className="h-4 w-4" />}
                        {company.billing_disabled ? "Включить биллинг" : "Отключить биллинг"}
                      </Button>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 xl:justify-end">
                    <Button
                      type="button"
                      variant="secondary"
                      disabled={statusMutation.isPending}
                      onClick={() => statusMutation.mutate({ companyId: company.id, status: "suspended" })}
                    >
                      <PauseCircle className="h-4 w-4" />
                      Приостановить
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      disabled={statusMutation.isPending}
                      onClick={() => statusMutation.mutate({ companyId: company.id, status: "active" })}
                    >
                      <PlayCircle className="h-4 w-4" />
                      Активировать
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </Panel>

      <Panel title="Каталог тарифов" description="Тарифы загружаются из внутренней биллинговой архитектуры.">
        <div className="grid gap-4 md:grid-cols-2">
          {planOptions.map((plan) => (
            <div key={plan.id} className="rounded-2xl border bg-muted/30 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-medium">{plan.name}</p>
                  <p className="text-sm text-muted-foreground">{plan.slug}</p>
                </div>
                <p className="text-sm font-medium">{formatMoney(plan.price_monthly, plan.currency)}</p>
              </div>
              <p className="mt-3 text-sm text-muted-foreground">{plan.description}</p>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
