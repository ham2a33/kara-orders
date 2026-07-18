"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactElement } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { confirmRecognition, getAIRecognition } from "@/lib/ai";
import { extractErrorMessage } from "@/lib/errors";

type DraftItem = {
  product_id: string;
  product_name: string;
  quantity: string;
  discount_amount: string;
  confidence: string;
  status: string;
  matched_product_name: string;
};

export default function AiReviewPage(): ReactElement {
  const params = useParams<{ recognitionId: string }>();
  const recognitionId = params.recognitionId;
  const router = useRouter();
  const queryClient = useQueryClient();
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [customerAddress, setCustomerAddress] = useState("");
  const [notes, setNotes] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [draftItems, setDraftItems] = useState<DraftItem[]>([]);

  const query = useQuery({
    queryKey: ["ai-recognition", recognitionId],
    queryFn: () => getAIRecognition(recognitionId),
    enabled: Boolean(recognitionId),
  });

  useEffect(() => {
    if (!query.data) {
      return;
    }
    setDraftItems(
      query.data.items.map((item) => ({
        product_id: item.matched_product?.id ?? "",
        product_name: item.product_name,
        quantity: String(item.quantity),
        discount_amount: "0",
        confidence: String(item.confidence),
        status: item.status,
        matched_product_name: item.matched_product?.name ?? "",
      })),
    );
  }, [query.data]);

  const confirmMutation = useMutation({
    mutationFn: () =>
      confirmRecognition(recognitionId, {
        customer_name: customerName.trim() || null,
        customer_phone: customerPhone.trim() || null,
        customer_address: customerAddress.trim() || null,
        notes: notes.trim() || null,
        status: "draft",
        items: draftItems.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
          discount_amount: item.discount_amount || 0,
        })),
      }),
    onSuccess: async (response) => {
      setMessage("Recognition converted into an order.");
      await queryClient.invalidateQueries({ queryKey: ["ai-history"] });
      router.push(`/orders/${response.order.id}`);
    },
  });

  const canConfirm = useMemo(
    () => draftItems.length > 0 && draftItems.every((item) => item.product_id.trim().length > 0),
    [draftItems],
  );

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <Badge>Review</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Review recognition {recognitionId}</h1>
        <p className="max-w-2xl text-muted-foreground">
          Confirm product matches, adjust quantities, and create the final order only after approval.
        </p>
      </section>

      {query.isError ? (
        <Card className="border-destructive/30">
          <CardContent className="p-5 text-sm text-destructive">{extractErrorMessage(query.error)}</CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Matched and unmatched items</CardTitle>
            <CardDescription>Product mapping stays editable until the order is confirmed.</CardDescription>
          </CardHeader>
          <CardContent className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[860px] text-left text-sm">
                <thead className="border-b text-muted-foreground">
                  <tr>
                    <th className="py-3 pr-4 font-medium">Product</th>
                    <th className="py-3 pr-4 font-medium">Matched product</th>
                    <th className="py-3 pr-4 font-medium">Product ID</th>
                    <th className="py-3 pr-4 font-medium">Quantity</th>
                    <th className="py-3 pr-4 font-medium">Confidence</th>
                    <th className="py-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {draftItems.map((item, index) => (
                    <tr key={`${item.product_name}-${index}`} className="border-b last:border-0">
                      <td className="py-4 pr-4 font-medium">{item.product_name}</td>
                      <td className="py-4 pr-4 text-muted-foreground">{item.matched_product_name || "—"}</td>
                      <td className="py-4 pr-4">
                        <Input
                          value={item.product_id}
                          onChange={(event) =>
                            setDraftItems((current) =>
                              current.map((currentItem, currentIndex) =>
                                currentIndex === index
                                  ? { ...currentItem, product_id: event.target.value }
                                  : currentItem,
                              ),
                            )
                          }
                          className="max-w-72"
                          placeholder="Paste product ID"
                        />
                      </td>
                      <td className="py-4 pr-4">
                        <Input
                          value={item.quantity}
                          onChange={(event) =>
                            setDraftItems((current) =>
                              current.map((currentItem, currentIndex) =>
                                currentIndex === index ? { ...currentItem, quantity: event.target.value } : currentItem,
                              ),
                            )
                          }
                          className="max-w-28"
                        />
                      </td>
                      <td className="py-4 pr-4 text-muted-foreground">{item.confidence}</td>
                      <td className="py-4">
                        <Badge
                          variant={
                            item.status === "matched"
                              ? "success"
                              : item.status === "needs_review"
                                ? "warning"
                                : "default"
                          }
                        >
                          {item.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Create order</CardTitle>
            <CardDescription>Confirm customer details before sending the order to the OrderService.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="customerName">Customer name</Label>
              <Input id="customerName" value={customerName} onChange={(event) => setCustomerName(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="customerPhone">Phone</Label>
              <Input id="customerPhone" value={customerPhone} onChange={(event) => setCustomerPhone(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="customerAddress">Address</Label>
              <Input
                id="customerAddress"
                value={customerAddress}
                onChange={(event) => setCustomerAddress(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <textarea
                id="notes"
                rows={4}
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                className="w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Priority delivery this afternoon."
              />
            </div>
            {message ? (
              <p className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-300">
                {message}
              </p>
            ) : null}
            {confirmMutation.isError ? (
              <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {extractErrorMessage(confirmMutation.error)}
              </p>
            ) : null}
            <div className="flex flex-col gap-3">
              <Button className="w-full" type="button" disabled={confirmMutation.isPending || !canConfirm} onClick={() => confirmMutation.mutate()}>
                {confirmMutation.isPending ? "Creating..." : "Create order"}
              </Button>
              <Button asChild variant="outline" className="w-full">
                <Link href="/ai/history">Back to history</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
