"use client";

import Link from "next/link";
import { useMemo, type ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";

import { formatVatLabel } from "@/components/products/catalog/catalog-modals";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getInventory, getInventoryHistory, getProduct, deleteProduct, restoreProduct } from "@/lib/products";
import { extractErrorMessage } from "@/lib/errors";
import { formatDate, formatMoney } from "@/components/platform/shared";

export default function ProductDetailsPage(): ReactElement {
  const params = useParams<{ productId: string }>();
  const productId = params.productId;
  const router = useRouter();
  const queryClient = useQueryClient();

  const productQuery = useQuery({
    queryKey: ["product", productId],
    queryFn: () => getProduct(productId),
    enabled: Boolean(productId),
  });
  const inventoryQuery = useQuery({
    queryKey: ["product-inventory", productId],
    queryFn: () => getInventory(productId),
    enabled: Boolean(productId),
  });
  const historyQuery = useQuery({
    queryKey: ["product-history", productId],
    queryFn: () => getInventoryHistory(productId),
    enabled: Boolean(productId),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProduct,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      router.push("/products");
    },
  });
  const restoreMutation = useMutation({
    mutationFn: restoreProduct,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      await queryClient.invalidateQueries({ queryKey: ["product", productId] });
    },
  });

  const product = productQuery.data;
  const metrics = useMemo(
    () => [
      {
        label: "Текущий остаток",
        value: `${inventoryQuery.data?.current_stock ?? product?.stock_qty ?? "0"} ${product?.unit ?? ""}`.trim(),
      },
      {
        label: "Стоимость склада",
        value: formatMoney(inventoryQuery.data?.stock_value ?? product?.stock_value ?? "0", product?.currency ?? "KZT"),
      },
      { label: "Цена продажи", value: formatMoney(product?.price ?? "0", product?.currency ?? "KZT") },
      { label: "Себестоимость", value: formatMoney(product?.cost ?? "0", product?.currency ?? "KZT") },
    ],
    [inventoryQuery.data?.current_stock, inventoryQuery.data?.stock_value, product],
  );

  const detailRows = useMemo(
    () => [
      { label: "Название", value: product?.name ?? "—" },
      { label: "SKU", value: product?.sku ?? "—" },
      { label: "Размер", value: product?.size ?? "—" },
      { label: "Производитель", value: product?.manufacturer ?? "—" },
      { label: "Категория", value: product?.category ?? "—" },
      {
        label: "Остаток",
        value: `${inventoryQuery.data?.current_stock ?? product?.stock_qty ?? "0"} ${product?.unit ?? ""}`.trim(),
      },
      { label: "Цена продажи", value: formatMoney(product?.price ?? "0", product?.currency ?? "KZT") },
      { label: "Себестоимость", value: product?.cost ? formatMoney(product.cost, product.currency) : "—" },
      { label: "НДС", value: formatVatLabel(product?.tax_rate) },
      { label: "Статус", value: product?.is_active ? "Активный" : "Неактивный" },
      { label: "Описание", value: product?.description?.trim() || "—" },
    ],
    [inventoryQuery.data?.current_stock, product],
  );

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <Badge>Детали товара</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">{product?.name ?? "Товар"}</h1>
            <p className="max-w-2xl text-muted-foreground">
              Полная карточка товара с остатками, ценами, НДС, изображениями и историей движений.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/products">К списку</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href={`/products/${productId}/edit`}>Редактировать товар</Link>
          </Button>
          {product?.deleted_at ? (
            <Button type="button" onClick={() => restoreMutation.mutate(productId)} disabled={restoreMutation.isPending}>
              Восстановить
            </Button>
          ) : (
            <Button type="button" variant="secondary" onClick={() => deleteMutation.mutate(productId)} disabled={deleteMutation.isPending}>
              Удалить
            </Button>
          )}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.label}>
            <CardHeader className="pb-2">
              <CardDescription>{metric.label}</CardDescription>
              <CardTitle className="text-3xl">{metric.value}</CardTitle>
            </CardHeader>
          </Card>
        ))}
      </section>

      {(productQuery.isError || inventoryQuery.isError || historyQuery.isError) ? (
        <Card className="border-destructive/30">
          <CardContent className="p-5 text-sm text-destructive">
            {extractErrorMessage(productQuery.error ?? inventoryQuery.error ?? historyQuery.error)}
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Сводка товара</CardTitle>
            <CardDescription>Основные поля каталога.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2 text-sm">
            {detailRows.map((row) => (
              <div key={row.label} className="grid gap-1 border-b border-dashed py-2 last:border-0 sm:grid-cols-[160px_1fr]">
                <span className="text-muted-foreground">{row.label}</span>
                <span className="font-medium">{row.value}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Изображения</CardTitle>
            <CardDescription>Основное изображение и дополнительные ракурсы.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            {(product?.images ?? []).length === 0 ? (
              <div className="aspect-[4/3] rounded-2xl border border-dashed bg-muted/20" />
            ) : (
              (product?.images ?? []).map((image) => (
                <div key={image.id} className="overflow-hidden rounded-2xl border">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={image.url} alt={image.alt_text ?? product?.name ?? "Product image"} className="aspect-[4/3] w-full object-cover" />
                  {image.is_primary ? <p className="px-3 py-2 text-xs text-muted-foreground">Основное изображение</p> : null}
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>История склада</CardTitle>
          <CardDescription>Последние движения остатков из backend-реестра.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {(historyQuery.data ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">История пока пуста.</p>
          ) : (
            (historyQuery.data ?? []).map((row) => (
              <div key={row.id} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border px-4 py-3">
                <div>
                  <p className="font-medium">{row.transaction_type}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatDate(row.created_at)} · {row.note ?? "Без заметки"}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-muted-foreground">{row.quantity} units</span>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
