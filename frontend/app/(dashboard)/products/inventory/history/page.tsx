"use client";

import { useEffect, useMemo, useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getInventoryHistory, getProducts } from "@/lib/products";
import { formatDate } from "@/components/platform/shared";

export default function InventoryHistoryPage(): ReactElement {
  const productsQuery = useQuery({
    queryKey: ["inventory-history-products"],
    queryFn: () => getProducts({ sortBy: "name", sortDir: "asc" }),
  });
  const products = useMemo(() => productsQuery.data?.items ?? [], [productsQuery.data?.items]);
  const [productId, setProductId] = useState<string>("");

  useEffect(() => {
    if (!productId && products.length > 0) {
      setProductId(products[0].id);
    }
  }, [productId, products]);

  const historyQuery = useQuery({
    queryKey: ["inventory-history", productId],
    queryFn: () => getInventoryHistory(productId),
    enabled: Boolean(productId),
  });

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <Badge>Inventory history</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Ledger timeline</h1>
        <p className="max-w-2xl text-muted-foreground">
          A transparent audit trail for stock movements, accounting, and warehouse reconciliation.
        </p>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Transactions</CardTitle>
          <CardDescription>Each movement maps directly to the inventory transaction endpoint.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <select
            className="h-11 rounded-xl border bg-background px-3 text-sm"
            value={productId}
            onChange={(event) => setProductId(event.target.value)}
          >
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.name}
              </option>
            ))}
          </select>

          <div className="grid gap-3">
            {(historyQuery.data ?? []).map((row) => (
              <div key={row.id} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border px-4 py-3">
                <div>
                  <p className="font-medium">{row.transaction_type}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatDate(row.created_at)} · {row.note ?? "No note"}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge
                    variant={
                      row.transaction_type === "stock_in"
                        ? "success"
                        : row.transaction_type === "stock_out"
                          ? "danger"
                          : "warning"
                    }
                  >
                    {row.transaction_type}
                  </Badge>
                  <span className="text-sm text-muted-foreground">{row.quantity}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
