"use client";

import Link from "next/link";
import { useMemo, useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getAIRecognitions } from "@/lib/ai";
import { formatDate } from "@/components/platform/shared";

function aiStatusLabel(status: string): string {
  switch (status) {
    case "completed":
      return "Готово";
    case "needs_review":
      return "На проверке";
    case "failed":
      return "Ошибка";
    case "converted":
      return "Создан заказ";
    default:
      return status;
  }
}

function statusVariant(status: string): "default" | "outline" | "success" | "warning" | "danger" {
  if (status === "converted" || status === "completed") {
    return "success";
  }
  if (status === "needs_review") {
    return "warning";
  }
  if (status === "failed") {
    return "danger";
  }
  return "outline";
}

export default function AiHistoryPage(): ReactElement {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [inputType, setInputType] = useState("");
  const query = useQuery({
    queryKey: ["ai-history", search, status, inputType],
    queryFn: () =>
      getAIRecognitions({
        search: search || undefined,
        status: status || undefined,
        inputType: inputType || undefined,
        pageSize: 20,
      }),
  });

  const count = useMemo(() => query.data?.total ?? 0, [query.data?.total]);

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <Badge>История AI</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">История распознаваний</h1>
        <p className="max-w-2xl text-muted-foreground">
          Просматривайте прошлые распознавания, уверенность модели и то, что уже было превращено в заказ.
        </p>
      </section>

      <Card>
        <CardHeader className="gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle>Последние распознавания</CardTitle>
            <CardDescription>Поиск, фильтры и аудит AI-истории из backend.</CardDescription>
          </div>
          <div className="flex gap-3">
            <Button asChild variant="outline">
              <Link href="/ai">Новое распознавание</Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <Input placeholder="Поиск распознаваний" value={search} onChange={(event) => setSearch(event.target.value)} />
          <select
            className="h-11 rounded-2xl border bg-background px-3 text-sm"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">Все статусы</option>
            <option value="completed">Готово</option>
            <option value="needs_review">Нужна проверка</option>
            <option value="failed">Ошибка</option>
            <option value="converted">Создан заказ</option>
          </select>
          <select
            className="h-11 rounded-2xl border bg-background px-3 text-sm"
            value={inputType}
            onChange={(event) => setInputType(event.target.value)}
          >
            <option value="">Все типы входа</option>
            <option value="photo">Фото</option>
            <option value="voice">Голос</option>
            <option value="text">Текст</option>
            <option value="pdf">PDF</option>
          </select>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="overflow-hidden p-0">
          <div className="border-b px-6 py-4">
            <p className="text-sm text-muted-foreground">Всего распознаваний: {count}</p>
          </div>

          <div className="grid gap-3 p-6 md:hidden">
            {(query.data?.items ?? []).map((item) => (
              <Link key={item.id} href={`/ai/review/${item.id}`} className="rounded-3xl border p-4 transition-colors hover:bg-muted/40">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <p className="text-sm font-medium">{item.id}</p>
                    <p className="text-sm text-muted-foreground capitalize">{item.input_type}</p>
                    <p className="text-xs text-muted-foreground">{formatDate(item.created_at)}</p>
                  </div>
                  <div className="text-right">
                    <Badge variant={statusVariant(item.status)}>{aiStatusLabel(item.status)}</Badge>
                    <p className="mt-2 text-sm text-muted-foreground">{item.confidence ?? "—"}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          <div className="hidden overflow-x-auto p-6 md:block">
            <table className="w-full text-left text-sm">
              <thead className="border-b text-muted-foreground">
                <tr>
                  <th className="py-3 pr-4 font-medium">ID</th>
                  <th className="py-3 pr-4 font-medium">Источник</th>
                  <th className="py-3 pr-4 font-medium">Статус</th>
                  <th className="py-3 pr-4 font-medium">Уверенность</th>
                  <th className="py-3 pr-4 font-medium">Заказ</th>
                  <th className="py-3 font-medium">Действие</th>
                </tr>
              </thead>
              <tbody>
                {(query.data?.items ?? []).map((item) => (
                  <tr key={item.id} className="border-b last:border-0">
                    <td className="py-4 pr-4 font-medium">{item.id}</td>
                    <td className="py-4 pr-4 text-muted-foreground capitalize">{item.input_type}</td>
                    <td className="py-4 pr-4">
                      <Badge variant={statusVariant(item.status)}>{aiStatusLabel(item.status)}</Badge>
                    </td>
                    <td className="py-4 pr-4 text-muted-foreground">{item.confidence ?? "—"}</td>
                    <td className="py-4 pr-4 text-muted-foreground">{item.created_order_id ?? "—"}</td>
                    <td className="py-4">
                      <Button asChild size="sm" variant="secondary">
                        <Link href={`/ai/review/${item.id}`}>Проверить</Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
