"use client";

import Link from "next/link";
import { useMemo, useState, type ReactElement } from "react";
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
      { label: "Active products", value: formatCount(products.filter((product) => product.is_active).length) },
      { label: "Low stock items", value: formatCount(products.filter((product) => product.low_stock).length) },
      { label: "Total products", value: formatCount(products.length) },
      {
        label: "Catalog value",
        value: formatMoney(
          products.reduce((total, product) => total + Number(product.stock_value || 0), 0).toFixed(2),
        ),
      },
    ],
    [products],
  );

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <Badge>Products & Inventory</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">Product catalog</h1>
            <p className="max-w-2xl text-muted-foreground">
              A clean workspace for managing products, categories, inventory, and the search flow used during order
              creation.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/products/categories">Categories</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/products/inventory">Inventory</Link>
          </Button>
          <Button asChild>
            <Link href="/products/new">Add product</Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <MetricCard key={stat.label} label={stat.label} value={stat.value} />
        ))}
      </section>

      <Panel title="Catalog overview" description="Search, filter, and manage the catalog from one focused surface.">
        <div className="grid gap-4 md:grid-cols-3">
          <Input placeholder="Search products" value={search} onChange={(event) => setSearch(event.target.value)} />
          <select
            className="h-11 rounded-xl border bg-background px-3 text-sm"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
          <select
            className="h-11 rounded-xl border bg-background px-3 text-sm"
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value)}
          >
            <option value="created_at">Newest</option>
            <option value="updated_at">Recently updated</option>
            <option value="name">Name</option>
            <option value="sku">SKU</option>
            <option value="price">Price</option>
            <option value="stock_qty">Stock</option>
          </select>
        </div>

        <div className="mt-6 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b text-muted-foreground">
                <tr>
                  <th className="py-3 pr-4 font-medium">Product</th>
                  <th className="py-3 pr-4 font-medium">SKU</th>
                  <th className="py-3 pr-4 font-medium">Category</th>
                  <th className="py-3 pr-4 font-medium">Stock</th>
                  <th className="py-3 pr-4 font-medium">Price</th>
                  <th className="py-3 font-medium">Status</th>
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
                        {product.low_stock ? "Low stock" : product.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Panel>
    </div>
  );
}
