"use client";

import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type AuthCardProps = {
  badge: string;
  title: string;
  description: string;
  children: ReactNode;
};

export function AuthCard({ badge, title, description, children }: AuthCardProps) {
  return (
    <div className="grid w-full gap-8 lg:grid-cols-[1fr_0.9fr]">
      <section className="space-y-6">
        <Badge>{badge}</Badge>
        <div className="space-y-3">
          <h1 className="text-4xl font-semibold tracking-tight">{title}</h1>
          <p className="max-w-xl text-lg text-muted-foreground">{description}</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Готовая аутентификация</CardTitle>
            <CardDescription>JWT access-токены, HTTP-only refresh cookie, валидация и tenant-aware перенаправления.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border bg-muted/40 p-4">
              <p className="text-sm font-medium">Безопасная сессия</p>
              <p className="text-sm text-muted-foreground">Access-токен открывает интерфейс, refresh-cookie продлевает сессию.</p>
            </div>
            <div className="rounded-2xl border bg-muted/40 p-4">
              <p className="text-sm font-medium">Проверка на сервере</p>
              <p className="text-sm text-muted-foreground">Ошибки API сразу показываются в форме для быстрого исправления.</p>
            </div>
          </CardContent>
        </Card>
      </section>

      <Card className="max-w-xl lg:justify-self-end">
        {children}
      </Card>
    </div>
  );
}
