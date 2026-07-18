"use client";

import Link from "next/link";
import { useMemo, type ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";

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
      { label: "Current stock", value: `${inventoryQuery.data?.current_stock ?? product?.stock_qty ?? "0"} ${product?.unit ?? ""}`.trim() },
      { label: "Inventory value", value: formatMoney(inventoryQuery.data?.stock_value ?? product?.stock_value ?? "0", product?.currency ?? "KZT") },
      { label: "Selling price", value: formatMoney(product?.price ?? "0", product?.currency ?? "KZT") },
      { label: "Tax rate", value: product?.tax_rate ? `${product.tax_rate}%` : "—" },
    ],
    [inventoryQuery.data?.current_stock, inventoryQuery.data?.stock_value, product],
  );

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <Badge>Product details</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">{product?.name ?? "Product"}</h1>
            <p className="max-w-2xl text-muted-foreground">
              Catalog item {productId} with inventory, pricing, images, and transaction history ready for the live API.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/products">Back to list</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href={`/products/${productId}/edit`}>Edit product</Link>
          </Button>
          {product?.deleted_at ? (
            <Button type="button" onClick={() => restoreMutation.mutate(productId)} disabled={restoreMutation.isPending}>
              Restore
            </Button>
          ) : (
            <Button type="button" variant="secondary" onClick={() => deleteMutation.mutate(productId)} disabled={deleteMutation.isPending}>
              Delete
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
            <CardTitle>Product summary</CardTitle>
            <CardDescription>Readable and concise for stockroom and sales teams.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>SKU: {product?.sku ?? "—"}</p>
            <p>Barcode: {product?.barcode ?? "—"}</p>
            <p>Category: {product?.category ?? "—"}</p>
            <p>Tags: {product?.tags.map((tag) => tag.name).join(", ") || "—"}</p>
            <p>Status: {product?.is_active ? "Active" : "Inactive"}</p>
            <p>Updated: {formatDate(product?.updated_at ?? null)}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Image set</CardTitle>
            <CardDescription>Primary image and additional catalog views.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            <div className="aspect-[4/3] rounded-2xl border border-dashed bg-muted/20" />
            <div className="grid gap-2 sm:grid-cols-2">
              <div className="rounded-2xl border bg-muted/30 p-4 text-sm">Main image</div>
              <div className="rounded-2xl border bg-muted/30 p-4 text-sm">Secondary image</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Inventory history</CardTitle>
          <CardDescription>Recent stock movements from the backend ledger.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3">
          {(historyQuery.data ?? []).map((row) => (
            <div key={row.id} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border px-4 py-3">
              <div>
                <p className="font-medium">{row.transaction_type}</p>
                <p className="text-sm text-muted-foreground">
                  {formatDate(row.created_at)} · {row.note ?? "No note"}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">{row.quantity} units</span>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
