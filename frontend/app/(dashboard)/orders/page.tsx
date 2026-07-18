"use client";

import Link from "next/link";
import { useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatCount, formatMoney, MetricCard, Panel } from "@/components/platform/shared";
import { getOrders } from "@/lib/orders";

export default function OrdersPage(): ReactElement {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const ordersQuery = useQuery({
    queryKey: ["orders", search, status, sortBy],
    queryFn: () =>
      getOrders({
        search: search || undefined,
        status: status || undefined,
        sortBy,
      }),
  });

  const orders = ordersQuery.data?.items ?? [];
  const stats = [
    { label: "Draft orders", value: formatCount(orders.filter((order) => order.status === "draft").length) },
    { label: "Confirmed", value: formatCount(orders.filter((order) => order.status === "confirmed").length) },
    { label: "Completed", value: formatCount(orders.filter((order) => order.status === "completed").length) },
    { label: "Cancelled", value: formatCount(orders.filter((order) => order.status === "cancelled").length) },
  ];

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <Badge>Orders & Invoices</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">Orders</h1>
            <p className="max-w-2xl text-muted-foreground">
              Manual order entry, review, saving, and invoice generation with a clean, fast workspace.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/orders/invoices">Invoice preview</Link>
          </Button>
          <Button asChild>
            <Link href="/orders/new">Create order</Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <MetricCard key={stat.label} label={stat.label} value={stat.value} />
        ))}
      </section>

      <Panel title="Recent orders" description="Search, sort, and filter the latest order history at a glance.">
        <div className="grid gap-4 md:grid-cols-3">
          <Input placeholder="Search orders" value={search} onChange={(event) => setSearch(event.target.value)} />
          <select
            className="h-11 rounded-xl border bg-background px-3 text-sm"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="confirmed">Confirmed</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <select
            className="h-11 rounded-xl border bg-background px-3 text-sm"
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value)}
          >
            <option value="created_at">Newest</option>
            <option value="updated_at">Recently updated</option>
            <option value="invoice_number">Invoice</option>
            <option value="customer_name">Customer</option>
            <option value="total">Total</option>
          </select>
        </div>

        <div className="mt-6 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b text-muted-foreground">
                <tr>
                  <th className="py-3 pr-4 font-medium">Invoice</th>
                  <th className="py-3 pr-4 font-medium">Customer</th>
                  <th className="py-3 pr-4 font-medium">Status</th>
                  <th className="py-3 pr-4 font-medium">Total</th>
                  <th className="py-3 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id} className="border-b last:border-0">
                    <td className="py-4 pr-4 font-medium">
                      <Link className="hover:underline" href={`/orders/${order.id}`}>
                        {order.invoice_number}
                      </Link>
                    </td>
                    <td className="py-4 pr-4 text-muted-foreground">{order.customer_name ?? "—"}</td>
                    <td className="py-4 pr-4">
                      <Badge
                        variant={
                          order.status === "completed"
                            ? "success"
                            : order.status === "confirmed"
                              ? "warning"
                              : order.status === "cancelled"
                                ? "danger"
                                : "default"
                        }
                      >
                        {order.status}
                      </Badge>
                    </td>
                    <td className="py-4 pr-4 text-muted-foreground">{formatMoney(order.total)}</td>
                    <td className="py-4 text-muted-foreground">{new Date(order.created_at).toLocaleDateString()}</td>
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
