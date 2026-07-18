"use client";

import Link from "next/link";
import { useMemo, type ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { deleteOrder, getOrder, restoreOrder } from "@/lib/orders";
import { extractErrorMessage } from "@/lib/errors";
import { formatDate, formatMoney } from "@/components/platform/shared";

export default function OrderDetailsPage(): ReactElement {
  const params = useParams<{ orderId: string }>();
  const orderId = params.orderId;
  const router = useRouter();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["order", orderId],
    queryFn: () => getOrder(orderId),
    enabled: Boolean(orderId),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteOrder,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["orders"] });
      await queryClient.invalidateQueries({ queryKey: ["order", orderId] });
      router.push("/orders");
    },
  });
  const restoreMutation = useMutation({
    mutationFn: restoreOrder,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["orders"] });
      await queryClient.invalidateQueries({ queryKey: ["order", orderId] });
    },
  });

  const order = query.data;
  const items = order?.items ?? [];
  const metrics = useMemo(
    () => [
      { label: "Status", value: order?.status ?? "—" },
      { label: "Subtotal", value: formatMoney(order?.subtotal ?? "0") },
      { label: "Tax", value: formatMoney(order?.tax_total ?? "0") },
      { label: "Total", value: formatMoney(order?.total ?? "0") },
    ],
    [order],
  );

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <Badge>Order details</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">{order?.invoice_number ?? orderId}</h1>
            <p className="max-w-2xl text-muted-foreground">
              Order {orderId} with line items, calculated totals, and invoice generation actions.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/orders">Back to orders</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href={`/orders/${orderId}/edit`}>Edit order</Link>
          </Button>
          <Button asChild>
            <Link href={`/orders/${orderId}/invoice`}>Invoice preview</Link>
          </Button>
          {order?.deleted_at ? (
            <Button type="button" onClick={() => restoreMutation.mutate(orderId)} disabled={restoreMutation.isPending}>
              Restore
            </Button>
          ) : (
            <Button type="button" variant="secondary" onClick={() => deleteMutation.mutate(orderId)} disabled={deleteMutation.isPending}>
              Delete
            </Button>
          )}
        </div>
      </section>

      {query.isError ? (
        <Card className="border-destructive/30">
          <CardContent className="p-5 text-sm text-destructive">{extractErrorMessage(query.error)}</CardContent>
        </Card>
      ) : null}

      <section className="grid gap-4 md:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.label}>
            <CardHeader>
              <CardDescription>{metric.label}</CardDescription>
              <CardTitle className="text-3xl">{metric.value}</CardTitle>
            </CardHeader>
          </Card>
        ))}
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <CardHeader>
            <CardTitle>Items</CardTitle>
            <CardDescription>Review the order lines exactly as the invoice engine will render them.</CardDescription>
          </CardHeader>
          <CardContent className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-left text-sm">
                <thead className="border-b text-muted-foreground">
                  <tr>
                    <th className="py-3 pr-4 font-medium">Product</th>
                    <th className="py-3 pr-4 font-medium">Qty</th>
                    <th className="py-3 pr-4 font-medium">Price</th>
                    <th className="py-3 pr-4 font-medium">Discount</th>
                    <th className="py-3 pr-4 font-medium">Tax</th>
                    <th className="py-3 font-medium">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id} className="border-b last:border-0">
                      <td className="py-4 pr-4 font-medium">{item.product_name}</td>
                      <td className="py-4 pr-4 text-muted-foreground">{item.quantity}</td>
                      <td className="py-4 pr-4 text-muted-foreground">{formatMoney(item.unit_price)}</td>
                      <td className="py-4 pr-4 text-muted-foreground">{formatMoney(item.discount_amount)}</td>
                      <td className="py-4 pr-4 text-muted-foreground">{formatMoney(item.tax_amount)}</td>
                      <td className="py-4 text-muted-foreground">{formatMoney(item.line_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Customer and invoice</CardTitle>
            <CardDescription>All invoice-ready information sits in one clean summary panel.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>Customer: {order?.customer_name ?? "—"}</p>
            <p>Phone: {order?.customer_phone ?? "—"}</p>
            <p>Address: {order?.customer_address ?? "—"}</p>
            <p>Notes: {order?.notes ?? "—"}</p>
            <p>Created at: {formatDate(order?.created_at ?? null)}</p>
            <p>Updated at: {formatDate(order?.updated_at ?? null)}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
