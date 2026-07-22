import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactElement } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AUTH_COOKIE_NAMES } from "@/lib/auth";

const modules = ["Аутентификация", "Главная", "Каталог", "Заказы", "Аналитика", "Настройки", "ИИ", "PDF"];

export default async function HomePage(): Promise<ReactElement> {
  const accessToken = (await cookies()).get(AUTH_COOKIE_NAMES.accessToken);
  if (accessToken) {
    redirect("/dashboard");
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(15,23,42,0.04),_transparent_35%),radial-gradient(circle_at_bottom_right,_rgba(2,132,199,0.08),_transparent_30%)]">
      <section className="mx-auto flex min-h-screen w-full max-w-7xl flex-col justify-center px-6 py-16 lg:px-10">
        <div className="grid gap-10 lg:grid-cols-[1.3fr_0.9fr] lg:items-center">
          <div className="max-w-3xl space-y-8">
            <Badge variant="default" className="bg-secondary text-secondary-foreground">
              Производственная SaaS-платформа
            </Badge>
            <div className="space-y-5">
              <h1 className="text-5xl font-semibold tracking-tight text-balance text-foreground sm:text-6xl">
                Kara Orders
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-muted-foreground sm:text-xl">
                Создавайте заказы и счета быстро, управляйте каталогом и ведите аккуратное мультиарендное рабочее пространство.
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <Button asChild>
                <Link href="/register">Создать аккаунт</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/login">Войти</Link>
              </Button>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {modules.map((module) => (
                <Card key={module} className="bg-card/80 backdrop-blur">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">{module}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription>
                      Построено для рабочих процессов с серверной валидацией и изоляцией компаний.
                    </CardDescription>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <Card className="overflow-hidden border border-border/70 bg-card/90">
            <CardHeader>
              <CardTitle>Готово к работе</CardTitle>
              <CardDescription>Быстрая аутентификация, защищённые маршруты и production API уже работают.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-2xl border bg-muted/40 p-4">
                <p className="text-sm font-medium">Backend</p>
                <p className="text-sm text-muted-foreground">
                  FastAPI, SQLAlchemy, Alembic, JWT и структурированное логирование.
                </p>
              </div>
              <div className="rounded-2xl border bg-muted/40 p-4">
                <p className="text-sm font-medium">Frontend</p>
                <p className="text-sm text-muted-foreground">
                  Next.js 15, TailwindCSS, shadcn/ui, формы и реальная интеграция с API.
                </p>
              </div>
              <div className="rounded-2xl border bg-muted/40 p-4">
                <p className="text-sm font-medium">Среда запуска</p>
                <p className="text-sm text-muted-foreground">Docker Compose с PostgreSQL, health checks и Nginx.</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  );
}
