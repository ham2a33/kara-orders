"use client";

import Link from "next/link";
import { useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiDownload } from "@/lib/api-client";
import { getInvoicePreview } from "@/lib/orders";
import { formatMoney } from "@/components/platform/shared";
import { extractErrorMessage } from "@/lib/errors";

export default function OrderInvoicePage(): ReactElement {
  const params = useParams<{ orderId: string }>();
  const orderId = params.orderId;
  const [isDownloading, setIsDownloading] = useState(false);
  const query = useQuery({
    queryKey: ["order-invoice", orderId],
    queryFn: () => getInvoicePreview(orderId),
    enabled: Boolean(orderId),
  });

  const downloadPdf = async (): Promise<void> => {
    setIsDownloading(true);
    try {
      await apiDownload(`/orders/${orderId}/invoice/pdf`, `invoice-${orderId}.pdf`);
    } finally {
      setIsDownloading(false);
    }
  };

  const preview = query.data;
  const order = preview?.order;

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <Badge>Invoice preview</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">Invoice PDF</h1>
            <p className="max-w-2xl text-muted-foreground">
              Preview the professional invoice generated for order {orderId}, then download or print it directly.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button type="button" variant="outline" onClick={downloadPdf} disabled={isDownloading}>
            {isDownloading ? "Downloading..." : "Download PDF"}
          </Button>
          <Button type="button" onClick={downloadPdf} disabled={isDownloading}>
            {isDownloading ? "Generating..." : "Print / regenerate"}
          </Button>
        </div>
      </section>

      {query.isError ? (
        <Card className="border-destructive/30">
          <CardContent className="p-5 text-sm text-destructive">{extractErrorMessage(query.error)}</CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="min-h-[720px]">
          <CardHeader>
            <CardTitle>Invoice canvas</CardTitle>
            <CardDescription>Styled to match the production PDF output.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="rounded-3xl border bg-muted/20 p-6">
              <div className="mb-6 flex items-start justify-between gap-6">
                <div>
                  <p className="text-sm text-muted-foreground">{preview?.company_name ?? "Company"}</p>
                  <h2 className="text-2xl font-semibold tracking-tight">{order?.invoice_number ?? `Order ${orderId}`}</h2>
                  <p className="text-sm text-muted-foreground">Date: {order ? new Date(order.created_at).toLocaleDateString() : "—"}</p>
                </div>
                <Badge variant="success">{order?.status ?? "Ready"}</Badge>
              </div>
              <div className="grid gap-6 md:grid-cols-2">
                <div>
                  <p className="text-sm font-medium">Company information</p>
                  <p className="text-sm text-muted-foreground">{preview?.company_name ?? "—"}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Customer information</p>
                  <p className="text-sm text-muted-foreground">{order?.customer_name ?? "—"}</p>
                  <p className="text-sm text-muted-foreground">{order?.customer_phone ?? "—"}</p>
                  <p className="text-sm text-muted-foreground">{order?.customer_address ?? "—"}</p>
                </div>
              </div>
              <div className="mt-6 overflow-hidden rounded-2xl border bg-background">
                <table className="w-full text-left text-sm">
                  <thead className="border-b bg-muted/30 text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3 font-medium">Product</th>
                      <th className="px-4 py-3 font-medium">Qty</th>
                      <th className="px-4 py-3 font-medium">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(order?.items ?? []).map((item) => (
                      <tr key={item.id} className="border-b last:border-0">
                        <td className="px-4 py-3">{item.product_name}</td>
                        <td className="px-4 py-3">{item.quantity}</td>
                        <td className="px-4 py-3">{formatMoney(item.line_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="rounded-3xl border bg-background p-6 text-sm text-muted-foreground">
              The backend PDF generator renders the final downloadable invoice with totals, footer, and payment details.
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Invoice actions</CardTitle>
            <CardDescription>Download, print, or regenerate a fresh invoice output.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border bg-muted/30 p-4">
              <p className="text-sm font-medium">PDF download</p>
              <p className="text-sm text-muted-foreground">Uses the backend `/invoice/pdf` endpoint with auth headers.</p>
            </div>
            <div className="rounded-2xl border bg-muted/30 p-4">
              <p className="text-sm font-medium">Print support</p>
              <p className="text-sm text-muted-foreground">Browser print can use the same PDF output.</p>
            </div>
            <div className="rounded-2xl border bg-muted/30 p-4">
              <p className="text-sm font-medium">Regeneration</p>
              <p className="text-sm text-muted-foreground">Invoices are regenerated from current order data on demand.</p>
            </div>
            <Button asChild variant="outline" className="w-full">
              <Link href={`/orders/${orderId}`}>Back to order</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
