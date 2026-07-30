"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  BulkDeleteModal,
  BulkPriceModal,
  BulkStatusModal,
  BulkVatModal,
  formatVatLabel,
} from "@/components/products/catalog/catalog-modals";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatCount, formatMoney, MetricCard, Panel } from "@/components/platform/shared";
import {
  bulkDeleteProducts,
  bulkUpdateProductPrices,
  bulkUpdateProductStatus,
  bulkUpdateProductVat,
  getProducts,
} from "@/lib/products";
import type { Product } from "@/types/products";

const PAGE_SIZE_OPTIONS = [
  { label: "20", value: 20 },
  { label: "50", value: 50 },
  { label: "100", value: 100 },
  { label: "Все", value: 0 },
] as const;

type SortColumn =
  | "created_at"
  | "name"
  | "manufacturer"
  | "category"
  | "stock_qty"
  | "price"
  | "cost"
  | "sku"
  | "is_active"
  | "tax_rate";

const TABLE_COLUMNS: Array<{ id: SortColumn; label: string }> = [
  { id: "name", label: "Товар" },
  { id: "manufacturer", label: "Производитель" },
  { id: "category", label: "Категория" },
  { id: "stock_qty", label: "Остаток" },
  { id: "price", label: "Цена" },
  { id: "cost", label: "Себестоимость" },
  { id: "sku", label: "SKU" },
  { id: "is_active", label: "Статус" },
  { id: "tax_rate", label: "НДС" },
];

function productStatusLabel(product: Product): string {
  if (product.low_stock) {
    return "Низкий остаток";
  }
  return product.is_active ? "Активный" : "Неактивный";
}

function productStatusVariant(product: Product): "warning" | "success" | "outline" {
  if (product.low_stock) {
    return "warning";
  }
  return product.is_active ? "success" : "outline";
}

export function CatalogPageClient(): ReactElement {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [sortBy, setSortBy] = useState<SortColumn>("created_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [priceModalOpen, setPriceModalOpen] = useState(false);
  const [vatModalOpen, setVatModalOpen] = useState(false);
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    setSearch(new URLSearchParams(window.location.search).get("search") ?? "");
  }, []);

  const listQueryKey = ["products", search, status, sortBy, sortDir, page, pageSize] as const;

  const productsQuery = useQuery({
    queryKey: listQueryKey,
    queryFn: () =>
      getProducts({
        page,
        pageSize,
        search: search || undefined,
        isActive: status === "" ? undefined : status === "active",
        sortBy,
        sortDir,
      }),
  });

  const products = useMemo(() => productsQuery.data?.items ?? [], [productsQuery.data?.items]);
  const total = productsQuery.data?.total ?? 0;
  const effectivePageSize = pageSize === 0 ? total || 20 : pageSize;
  const totalPages = Math.max(Math.ceil(total / effectivePageSize), 1);
  const rangeStart = total === 0 ? 0 : (page - 1) * effectivePageSize + 1;
  const rangeEnd = Math.min(page * effectivePageSize, total);

  const selectedCount = selectedIds.size;
  const selectedOnPageCount = products.filter((product) => selectedIds.has(product.id)).length;
  const allOnPageSelected = products.length > 0 && selectedOnPageCount === products.length;

  const stats = useMemo(
    () => [
      { label: "Активные товары", value: formatCount(products.filter((product) => product.is_active).length) },
      { label: "Низкий остаток", value: formatCount(products.filter((product) => product.low_stock).length) },
      { label: "Всего товаров", value: formatCount(total) },
      {
        label: "Стоимость на странице",
        value: formatMoney(
          products.reduce((sum, product) => sum + Number(product.stock_value || 0), 0).toFixed(2),
        ),
      },
    ],
    [products, total],
  );

  const invalidateCatalog = async () => {
    await queryClient.invalidateQueries({ queryKey: ["products"] });
  };

  const priceMutation = useMutation({
    mutationFn: bulkUpdateProductPrices,
    onSuccess: async () => {
      setPriceModalOpen(false);
      setSelectedIds(new Set());
      await invalidateCatalog();
    },
  });

  const vatMutation = useMutation({
    mutationFn: bulkUpdateProductVat,
    onSuccess: async () => {
      setVatModalOpen(false);
      setSelectedIds(new Set());
      await invalidateCatalog();
    },
  });

  const statusMutation = useMutation({
    mutationFn: bulkUpdateProductStatus,
    onSuccess: async () => {
      setStatusModalOpen(false);
      setSelectedIds(new Set());
      await invalidateCatalog();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: bulkDeleteProducts,
    onSuccess: async () => {
      setDeleteModalOpen(false);
      setSelectedIds(new Set());
      await invalidateCatalog();
    },
  });

  const toggleSort = (column: SortColumn) => {
    if (sortBy === column) {
      setSortDir((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortBy(column);
    setSortDir("asc");
    setPage(1);
  };

  const toggleProductSelection = (productId: string) => {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(productId)) {
        next.delete(productId);
      } else {
        next.add(productId);
      }
      return next;
    });
  };

  const toggleSelectAllOnPage = () => {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (allOnPageSelected) {
        products.forEach((product) => next.delete(product.id));
      } else {
        products.forEach((product) => next.add(product.id));
      }
      return next;
    });
  };

  const selectedIdList = useMemo(() => Array.from(selectedIds), [selectedIds]);

  const openBulkAction = (action: "price" | "vat" | "status" | "delete") => {
    if (selectedCount === 0) {
      return;
    }
    if (action === "price") setPriceModalOpen(true);
    if (action === "vat") setVatModalOpen(true);
    if (action === "status") setStatusModalOpen(true);
    if (action === "delete") setDeleteModalOpen(true);
  };

  const sortIndicator = (column: SortColumn) => {
    if (sortBy !== column) {
      return " ↕";
    }
    return sortDir === "asc" ? " ↑" : " ↓";
  };

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
            <Link href="/products/import">Импорт</Link>
          </Button>
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
        <div className="flex flex-col gap-4">
          <div className="grid gap-4 md:grid-cols-[1fr_auto_auto]">
            <Input
              placeholder="Поиск товаров"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
            />
            <select
              className="h-11 rounded-2xl border bg-background px-3 text-sm"
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                setPage(1);
              }}
            >
              <option value="">Все статусы</option>
              <option value="active">Активный</option>
              <option value="inactive">Неактивный</option>
            </select>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" disabled={selectedCount === 0} onClick={() => openBulkAction("price")}>
                Изменить цены
              </Button>
              <Button type="button" variant="outline" disabled={selectedCount === 0} onClick={() => openBulkAction("vat")}>
                Изменить НДС
              </Button>
            </div>
          </div>

          {selectedCount > 0 ? (
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border bg-muted/30 px-4 py-3">
              <p className="text-sm font-medium">Выбрано: {selectedCount} товаров</p>
              <div className="flex flex-wrap gap-2">
                <Button type="button" size="sm" variant="outline" onClick={() => openBulkAction("price")}>
                  Изменить цены
                </Button>
                <Button type="button" size="sm" variant="outline" onClick={() => openBulkAction("vat")}>
                  Изменить НДС
                </Button>
                <Button type="button" size="sm" variant="outline" onClick={() => openBulkAction("status")}>
                  Изменить статус
                </Button>
                <Button type="button" size="sm" variant="secondary" onClick={() => openBulkAction("delete")}>
                  Удалить
                </Button>
              </div>
            </div>
          ) : null}
        </div>

        <div className="mt-6 grid gap-3 md:hidden">
          {products.map((product) => (
            <div key={product.id} className="rounded-3xl border p-4">
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  checked={selectedIds.has(product.id)}
                  onChange={() => toggleProductSelection(product.id)}
                  aria-label={`Выбрать ${product.name}`}
                />
                <Link href={`/products/${product.id}`} className="flex-1 transition-colors hover:bg-muted/40">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <p className="text-base font-medium">{product.name}</p>
                      <p className="text-sm text-muted-foreground">{product.manufacturer ?? "Без производителя"}</p>
                      <p className="text-sm text-muted-foreground">{product.sku ?? "Без SKU"}</p>
                      <p className="text-xs text-muted-foreground">
                        {product.category ?? "Без категории"} • {product.stock_qty ?? "0"} {product.unit} •{" "}
                        {formatVatLabel(product.tax_rate)}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge variant={productStatusVariant(product)}>{productStatusLabel(product)}</Badge>
                      <p className="mt-2 text-sm font-medium">{formatMoney(product.price, product.currency)}</p>
                      <p className="text-xs text-muted-foreground">
                        Себест.: {product.cost ? formatMoney(product.cost, product.currency) : "—"}
                      </p>
                    </div>
                  </div>
                </Link>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 hidden md:block overflow-x-auto">
          <table className="w-full min-w-[960px] text-left text-sm">
            <thead className="border-b text-muted-foreground">
              <tr>
                <th className="py-3 pr-3 font-medium">
                  <input
                    type="checkbox"
                    checked={allOnPageSelected}
                    onChange={toggleSelectAllOnPage}
                    aria-label="Выбрать все на странице"
                  />
                </th>
                {TABLE_COLUMNS.map((column) => (
                  <th key={column.id} className="py-3 pr-4 font-medium">
                    <button type="button" className="inline-flex items-center hover:text-foreground" onClick={() => toggleSort(column.id)}>
                      {column.label}
                      <span className="text-xs">{sortIndicator(column.id)}</span>
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id} className="border-b last:border-0">
                  <td className="py-4 pr-3">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(product.id)}
                      onChange={() => toggleProductSelection(product.id)}
                      aria-label={`Выбрать ${product.name}`}
                    />
                  </td>
                  <td className="py-4 pr-4 font-medium">
                    <Link className="hover:underline" href={`/products/${product.id}`}>
                      {product.name}
                    </Link>
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">{product.manufacturer ?? "—"}</td>
                  <td className="py-4 pr-4 text-muted-foreground">{product.category ?? "—"}</td>
                  <td className="py-4 pr-4 text-muted-foreground">
                    {product.stock_qty ?? "0"} {product.unit}
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">{formatMoney(product.price, product.currency)}</td>
                  <td className="py-4 pr-4 text-muted-foreground">
                    {product.cost ? formatMoney(product.cost, product.currency) : "—"}
                  </td>
                  <td className="py-4 pr-4 text-muted-foreground">{product.sku ?? "—"}</td>
                  <td className="py-4 pr-4">
                    <Badge variant={productStatusVariant(product)}>{productStatusLabel(product)}</Badge>
                  </td>
                  <td className="py-4 text-muted-foreground">{formatVatLabel(product.tax_rate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-muted-foreground">
            {total === 0 ? "0 товаров" : `${rangeStart}–${rangeEnd} из ${total} товаров`}
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              На странице
              <select
                className="h-9 rounded-xl border bg-background px-2"
                value={pageSize}
                onChange={(event) => {
                  setPageSize(Number(event.target.value));
                  setPage(1);
                }}
              >
                {PAGE_SIZE_OPTIONS.map((option) => (
                  <option key={option.label} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex gap-2">
              <Button type="button" variant="outline" disabled={page <= 1} onClick={() => setPage((current) => Math.max(current - 1, 1))}>
                Назад
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={page >= totalPages}
                onClick={() => setPage((current) => Math.min(current + 1, totalPages))}
              >
                Вперёд
              </Button>
            </div>
          </div>
        </div>
      </Panel>

      <BulkPriceModal
        open={priceModalOpen}
        selectedCount={selectedCount}
        pending={priceMutation.isPending}
        onClose={() => setPriceModalOpen(false)}
        onConfirm={(payload) =>
          priceMutation.mutate({
            product_ids: selectedIdList,
            field: payload.field,
            operation: payload.operation,
            mode: payload.mode,
            value: payload.value,
          })
        }
      />
      <BulkVatModal
        open={vatModalOpen}
        selectedCount={selectedCount}
        pending={vatMutation.isPending}
        onClose={() => setVatModalOpen(false)}
        onConfirm={(taxRate) =>
          vatMutation.mutate({
            product_ids: selectedIdList,
            tax_rate: taxRate,
          })
        }
      />
      <BulkStatusModal
        open={statusModalOpen}
        selectedCount={selectedCount}
        pending={statusMutation.isPending}
        onClose={() => setStatusModalOpen(false)}
        onConfirm={(isActive) =>
          statusMutation.mutate({
            product_ids: selectedIdList,
            is_active: isActive,
          })
        }
      />
      <BulkDeleteModal
        open={deleteModalOpen}
        selectedCount={selectedCount}
        pending={deleteMutation.isPending}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={() => deleteMutation.mutate(selectedIdList)}
      />
    </div>
  );
}
