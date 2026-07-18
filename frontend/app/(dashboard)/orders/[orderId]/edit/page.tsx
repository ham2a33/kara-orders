"use client";

import { useEffect, useMemo, useState, type ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { extractErrorMessage } from "@/lib/errors";
import { getOrder, updateOrder } from "@/lib/orders";

type DraftItem = {
  product_id: string;
  quantity: string;
  discount_amount: string;
};

export default function OrderEditPage(): ReactElement {
  const params = useParams<{ orderId: string }>();
  const orderId = params.orderId;
  const router = useRouter();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["order", orderId],
    queryFn: () => getOrder(orderId),
    enabled: Boolean(orderId),
  });

  const order = query.data;
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [customerAddress, setCustomerAddress] = useState("");
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<"draft" | "confirmed" | "completed" | "cancelled">("draft");
  const [items, setItems] = useState<DraftItem[]>([]);

  useEffect(() => {
    if (!order) {
      return;
    }
    setCustomerName(order.customer_name ?? "");
    setCustomerPhone(order.customer_phone ?? "");
    setCustomerAddress(order.customer_address ?? "");
    setNotes(order.notes ?? "");
    setStatus(order.status);
    setItems(
      order.items.map((item) => ({
        product_id: item.product_id ?? "",
        quantity: item.quantity,
        discount_amount: item.discount_amount,
      })),
    );
  }, [order]);

  const canSubmit = useMemo(
    () => items.length > 0 && items.every((item) => item.product_id.trim().length > 0 && Number(item.quantity) > 0),
    [items],
  );

  const mutation = useMutation({
    mutationFn: () =>
      updateOrder(orderId, {
        customer_name: customerName.trim() || null,
        customer_phone: customerPhone.trim() || null,
        customer_address: customerAddress.trim() || null,
        notes: notes.trim() || null,
        status,
        items: items.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
          discount_amount: item.discount_amount || 0,
        })),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["orders"] });
      await queryClient.invalidateQueries({ queryKey: ["order", orderId] });
      router.push(`/orders/${orderId}`);
    },
  });

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <Badge>Edit order</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Update order</h1>
        <p className="max-w-2xl text-muted-foreground">
          Edit customer details, quantities, discounts, and items for order {orderId}.
        </p>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Editable order</CardTitle>
          <CardDescription>The backend recalculates all totals before saving.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="editCustomerName">Customer name</Label>
            <Input id="editCustomerName" value={customerName} onChange={(event) => setCustomerName(event.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="editCustomerPhone">Phone</Label>
            <Input id="editCustomerPhone" value={customerPhone} onChange={(event) => setCustomerPhone(event.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="editCustomerAddress">Address</Label>
            <Input
              id="editCustomerAddress"
              value={customerAddress}
              onChange={(event) => setCustomerAddress(event.target.value)}
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="editStatus">Status</Label>
            <select
              id="editStatus"
              className="flex h-11 w-full rounded-2xl border border-input bg-background px-4 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
              value={status}
              onChange={(event) => setStatus(event.target.value as typeof status)}
            >
              <option value="draft">Draft</option>
              <option value="confirmed">Confirmed</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="editNotes">Notes</Label>
            <textarea
              id="editNotes"
              rows={4}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              className="w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>
          <div className="rounded-2xl border bg-muted/30 p-4 text-sm text-muted-foreground md:col-span-2">
            Item editor and review grid is connected to the live order API below.
          </div>
          <div className="md:col-span-2 space-y-4">
            {items.map((item, index) => (
              <div key={index} className="grid gap-3 rounded-2xl border p-4 md:grid-cols-3">
                <div className="space-y-2 md:col-span-3">
                  <Label>Product ID</Label>
                  <Input
                    value={item.product_id}
                    onChange={(event) =>
                      setItems((current) =>
                        current.map((currentItem, currentIndex) =>
                          currentIndex === index ? { ...currentItem, product_id: event.target.value } : currentItem,
                        ),
                      )
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>Quantity</Label>
                  <Input
                    value={item.quantity}
                    onChange={(event) =>
                      setItems((current) =>
                        current.map((currentItem, currentIndex) =>
                          currentIndex === index ? { ...currentItem, quantity: event.target.value } : currentItem,
                        ),
                      )
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>Discount</Label>
                  <Input
                    value={item.discount_amount}
                    onChange={(event) =>
                      setItems((current) =>
                        current.map((currentItem, currentIndex) =>
                          currentIndex === index ? { ...currentItem, discount_amount: event.target.value } : currentItem,
                        ),
                      )
                    }
                  />
                </div>
                <div className="flex justify-end md:col-span-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setItems((current) => current.filter((_, currentIndex) => currentIndex !== index))}
                    disabled={items.length === 1}
                  >
                    Remove line
                  </Button>
                </div>
              </div>
            ))}
            <Button type="button" variant="outline" onClick={() => setItems((current) => [...current, { product_id: "", quantity: "1", discount_amount: "0" }])}>
              Add line
            </Button>
          </div>
          {mutation.isError ? (
            <p className="md:col-span-2 rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {extractErrorMessage(mutation.error)}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-3 md:col-span-2">
            <Button type="button" onClick={() => mutation.mutate()} disabled={mutation.isPending || !canSubmit}>
              {mutation.isPending ? "Saving..." : "Save order"}
            </Button>
            <Button type="button" variant="outline" onClick={() => router.back()}>
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
