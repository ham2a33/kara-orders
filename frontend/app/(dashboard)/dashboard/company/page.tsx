"use client";

import Link from "next/link";
import type { ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getCompanyUsers, getMyCompany } from "@/lib/company";
import { formatDate, formatCount } from "@/components/platform/shared";
import { extractErrorMessage } from "@/lib/errors";

export default function CompanyProfilePage(): ReactElement {
  const companyQuery = useQuery({
    queryKey: ["company-profile"],
    queryFn: getMyCompany,
  });

  const usersQuery = useQuery({
    queryKey: ["company-users"],
    queryFn: getCompanyUsers,
  });

  const company = companyQuery.data;
  const activeUsers = usersQuery.data?.items.filter((user) => user.is_active && !user.deleted_at).length ?? 0;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <Badge className="w-fit">Профиль компании</Badge>
          <CardTitle>{company?.name ?? "Профиль компании"}</CardTitle>
          <CardDescription>
            Держите профиль компании, брендинг и настройки счетов в соответствии с тем, как команда работает на самом деле.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border bg-muted/40 p-4">
            <p className="text-sm text-muted-foreground">Активные пользователи</p>
            <p className="mt-2 text-2xl font-semibold">{formatCount(activeUsers)}</p>
          </div>
          <div className="rounded-2xl border bg-muted/40 p-4">
            <p className="text-sm text-muted-foreground">Валюта</p>
            <p className="mt-2 text-2xl font-semibold">{company?.currency ?? "—"}</p>
          </div>
          <div className="rounded-2xl border bg-muted/40 p-4">
            <p className="text-sm text-muted-foreground">Обновлено</p>
            <p className="mt-2 text-2xl font-semibold">{formatDate(company?.updated_at ?? null)}</p>
          </div>
        </CardContent>
      </Card>

      {companyQuery.isError ? (
        <Card className="border-destructive/30">
          <CardContent className="p-5 text-sm text-destructive">
            {extractErrorMessage(companyQuery.error)}
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
        <Card>
          <CardHeader>
            <CardTitle>Сводка компании</CardTitle>
            <CardDescription>Основные данные, используемые в счетах, заказах и приглашениях.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            {[
              ["Название компании", company?.name ?? "—"],
              ["Эл. почта", company?.email ?? "—"],
              ["Телефон", company?.phone ?? "—"],
              ["Сайт", company?.website ?? "—"],
              ["Часовой пояс", company?.timezone ?? "—"],
              ["Язык", company?.language ?? "—"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl border bg-muted/30 p-4">
                <p className="text-sm text-muted-foreground">{label}</p>
                <p className="mt-1 text-sm font-medium">{value}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Быстрые действия</CardTitle>
            <CardDescription>Переходите в отдельные разделы управления компанией.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            <Button asChild variant="outline" className="justify-start">
              <Link href="/settings/store">Информация магазина</Link>
            </Button>
            <Button asChild className="justify-start">
              <Link href="/dashboard/company/settings">Открыть настройки</Link>
            </Button>
            <Button asChild variant="outline" className="justify-start">
              <Link href="/dashboard/company/branding">Брендинг</Link>
            </Button>
            <Button asChild variant="outline" className="justify-start">
              <Link href="/dashboard/company/invoice-settings">Настройки счетов</Link>
            </Button>
            <Button asChild variant="outline" className="justify-start">
              <Link href="/dashboard/company/users">Управление пользователями</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
