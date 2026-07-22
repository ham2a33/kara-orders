"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatCount, formatMoney, MetricCard, Panel } from "@/components/platform/shared";
import { getProducts } from "@/lib/products";

export default function ProductsPage(): ReactElement {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [sortBy, setSortBy] = useState("created_at");

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    setSearch(new URLSearchParams(window.location.search).get("search") ?? "");
  }, []);

  const productsQuery = useQuery({
    queryKey: ["products", search, status, sortBy],
    queryFn: () =>
      getProducts({
        search: search || undefined,
        isActive: status === "" ? undefined : status === "active",
        sortBy,
      }),
  });

  const products = useMemo(() => productsQuery.data?.items ?? [], [productsQuery.data?.items]);
  const stats = useMemo(
    () => [
      { label: "Активные товары", value: formatCount(products.filter((product) => product.is_active).length) },
      { label: "Низкий остаток", value: formatCount(products.filter((product) => product.low_stock).length) },
      { label: "Всего товаров", value: formatCount(products.length) },
      {
        label: "Стоимость каталога",
        value: formatMoney(
          products.reduce((total, product) => total + Number(product.stock_value || 0), 0).toFixed(2),
        ),
      },
    ],
    [products],
  );

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <Badge>Каталог и склад</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">Каталог товаров</h1>
            <p className="max-w-2xl text-muted-foreground">
              Спокойное рабочее пространство для управления товарами, категориями, запасами и поиском во время создания заказа.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/products/categories">Категории</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/products/inventory">Склад</Link>
          </Button>
          <Button asChild>
            <Link href="/products/new">Добавить товар</Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <MetricCard key={stat.label} label={stat.label} value={stat.value} />
        ))}
      </section>

      <Panel title="Обзор каталога" description="Поиск, фильтрация и управление товарами без лишнего шума.">
        <div className="grid gap-4 md:grid-cols-3">
          <Input placeholder="Поиск товаров" value={search} onChange={(event) => setSearch(event.target.value)} />
          <select
            className="h-11 rounded-2xl border bg-background px-3 text-sm"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">Все статусы</option>
            <option value="active">Активный</option>
            <option value="inactive">Неактивный</option>
          </select>
          <select
            className="h-11 rounded-2xl border bg-background px-3 text-sm"
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value)}
          >
            <option value="created_at">Сначала новые</option>
            <option value="updated_at">Недавно обновлённые</option>
            <option value="name">По названию</option>
            <option value="sku">По SKU</option>
            <option value="price">По цене</option>
            <option value="stock_qty">По остатку</option>
          </select>
        </div>

        <div className="mt-6 grid gap-3 md:hidden">
          {products.map((product) => (
            <Link key={product.id} href={`/products/${product.id}`} className="rounded-3xl border p-4 transition-colors hover:bg-muted/40">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <p className="text-base font-medium">{product.name}</p>
                  <p className="text-sm text-muted-foreground">{product.manufacturer ?? "Без производителя"}</p>
                  <p className="text-sm text-muted-foreground">{product.sku ?? "Без SKU"}</p>
                  <p className="text-xs text-muted-foreground">
                    {product.category ?? "Без категории"} • {product.stock_qty ?? "0"} {product.unit}
                  </p>
                </div>
                <div className="text-right">
                  <Badge variant={product.low_stock ? "warning" : product.is_active ? "success" : "outline"}>
                    {product.low_stock ? "Низкий остаток" : product.is_active ? "Активный" : "Неактивный"}
                  </Badge>
                  <p className="mt-2 text-sm font-medium">{formatMoney(product.price, product.currency)}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>

        <div className="mt-6 hidden md:block">
          <table className="w-full text-left text-sm">
            <thead className="border-b text-muted-foreground">
              <tr>
                <th className="py-3 pr-4 font-medium">Товар</th>
                <th className="py-3 pr-4 font-medium">Производитель</th>
                <th className="py-3 pr-4 font-medium">SKU</th>
                <th className="py-3 pr-4 font-medium">Категория</th>
                <th className="py-3 pr-4 font-medium">Остаток</th>
                <th className="py-3 pr-4 font-medium">Цена</th>
                <th className="py-3 font-medium">Статус</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id} className="border-b last:border-0">
                  <td className="py-4 pr-4 font-medium">
                    <Link className="hover:underline" href={`/products/${product.id}`}>
                      {product.name}
                    </Link>
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">{product.manufacturer ?? "—"}</td>
                  <td className="py-4 pr-4 text-muted-foreground">{product.sku ?? "—"}</td>
                  <td className="py-4 pr-4 text-muted-foreground">{product.category ?? "—"}</td>
                  <td className="py-4 pr-4 text-muted-foreground">
                    {product.stock_qty ?? "0"} {product.unit}
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">
                    {formatMoney(product.price, product.currency)}
                  </td>
                  <td className="py-4">
                    <Badge variant={product.low_stock ? "warning" : product.is_active ? "success" : "outline"}>
                      {product.low_stock ? "Низкий остаток" : product.is_active ? "Активный" : "Неактивный"}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
