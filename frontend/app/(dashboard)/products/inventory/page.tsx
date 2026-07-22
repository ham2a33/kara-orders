"use client";

import Link from "next/link";
import { useMemo, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getProducts } from "@/lib/products";
import { formatCount, formatMoney } from "@/components/platform/shared";

export default function InventoryPage(): ReactElement {
  const productsQuery = useQuery({
    queryKey: ["inventory-products"],
    queryFn: () => getProducts({ sortBy: "stock_qty", sortDir: "desc" }),
  });

  const products = useMemo(() => productsQuery.data?.items ?? [], [productsQuery.data?.items]);
  const summary = useMemo(
    () => ({
      totalStockValue: products.reduce((total, product) => total + Number(product.stock_value || 0), 0),
      lowStock: products.filter((product) => product.low_stock).length,
      movementsToday: products.length,
    }),
    [products],
  );

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <Badge>Склад</Badge>
          <h1 className="text-3xl font-semibold tracking-tight">Обзор остатков</h1>
          <p className="max-w-2xl text-muted-foreground">
            Остатки, предупреждения о низком запасе и история подключены к backend-реестру склада.
          </p>
        </div>
        <div className="flex gap-3">
          <Button asChild variant="outline">
            <Link href="/products/inventory/history">История</Link>
          </Button>
          <Button asChild>
            <Link href="/products/new">Изменить остаток</Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardDescription>Общая стоимость склада</CardDescription>
            <CardTitle className="text-3xl">{formatMoney(String(summary.totalStockValue))}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Позиции с низким запасом</CardDescription>
            <CardTitle className="text-3xl">{formatCount(summary.lowStock)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Строки склада</CardDescription>
            <CardTitle className="text-3xl">{formatCount(summary.movementsToday)}</CardTitle>
          </CardHeader>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Текущий остаток</CardTitle>
          <CardDescription>Простой контроль склада для занятых команд.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {products.map((row) => (
            <div key={row.id} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border px-4 py-3">
              <div>
                <p className="font-medium">{row.name}</p>
                <p className="text-sm text-muted-foreground">{formatMoney(row.stock_value, row.currency)}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">
                  {row.stock_qty ?? "0"} {row.unit}
                </span>
                <Badge variant={row.low_stock ? "warning" : "success"}>{row.low_stock ? "Низкий запас" : "В норме"}</Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
