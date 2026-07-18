"use client";

import { useEffect, useState, type ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { extractErrorMessage } from "@/lib/errors";
import { getProduct, updateProduct } from "@/lib/products";

type FormState = {
  name: string;
  sku: string;
  barcode: string;
  category: string;
  unit: string;
  currency: string;
  price: string;
  cost: string;
  tax_rate: string;
  stock_qty: string;
  low_stock_threshold: string;
  is_active: boolean;
};

const editFields: Array<{ id: Exclude<keyof FormState, "is_active">; label: string; span?: boolean }> = [
  { id: "name", label: "Product name", span: true },
  { id: "sku", label: "SKU" },
  { id: "barcode", label: "Barcode" },
  { id: "category", label: "Category" },
  { id: "unit", label: "Unit" },
  { id: "currency", label: "Currency" },
  { id: "price", label: "Selling price" },
  { id: "cost", label: "Cost price" },
  { id: "tax_rate", label: "Tax rate" },
  { id: "stock_qty", label: "Opening stock" },
  { id: "low_stock_threshold", label: "Low stock threshold" },
];

export default function ProductEditPage(): ReactElement {
  const params = useParams<{ productId: string }>();
  const productId = params.productId;
  const router = useRouter();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["product", productId],
    queryFn: () => getProduct(productId),
    enabled: Boolean(productId),
  });
  const product = query.data;
  const [formState, setFormState] = useState<FormState>({
    name: "",
    sku: "",
    barcode: "",
    category: "",
    unit: "pcs",
    currency: "KZT",
    price: "",
    cost: "",
    tax_rate: "",
    stock_qty: "",
    low_stock_threshold: "",
    is_active: true,
  });

  useEffect(() => {
    if (!product) {
      return;
    }
    setFormState({
      name: product.name ?? "",
      sku: product.sku ?? "",
      barcode: product.barcode ?? "",
      category: product.category ?? "",
      unit: product.unit ?? "pcs",
      currency: product.currency ?? "KZT",
      price: product.price ?? "",
      cost: product.cost ?? "",
      tax_rate: product.tax_rate ?? "",
      stock_qty: product.stock_qty ?? "",
      low_stock_threshold: product.low_stock_threshold ?? "",
      is_active: product.is_active,
    });
  }, [product]);

  const mutation = useMutation({
    mutationFn: () =>
      updateProduct(productId, {
        name: formState.name.trim(),
        sku: formState.sku.trim() || null,
        barcode: formState.barcode.trim() || null,
        category: formState.category.trim() || null,
        unit: formState.unit.trim(),
        currency: formState.currency.trim().toUpperCase(),
        price: formState.price,
        cost: formState.cost || null,
        tax_rate: formState.tax_rate || null,
        stock_qty: formState.stock_qty || null,
        low_stock_threshold: formState.low_stock_threshold || null,
        is_active: formState.is_active,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      await queryClient.invalidateQueries({ queryKey: ["product", productId] });
      router.push(`/products/${productId}`);
    },
  });

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <Badge>Editor</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Edit product</h1>
        <p className="max-w-2xl text-muted-foreground">
          Update product {productId} with the same clean entry experience used for new catalog items.
        </p>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Editable fields</CardTitle>
          <CardDescription>All fields map directly to the API and database model.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          {editFields.map((field) => (
            <div key={field.id} className={`space-y-2 ${field.span ? "md:col-span-2" : ""}`}>
              <Label htmlFor={`edit-${field.id}`}>{field.label}</Label>
              <Input
                id={`edit-${field.id}`}
                value={String(formState[field.id])}
                onChange={(event) => setFormState((current) => ({ ...current, [field.id]: event.target.value }))}
              />
            </div>
          ))}
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="edit-status">Status</Label>
            <select
              id="edit-status"
              className="flex h-11 w-full rounded-2xl border border-input bg-background px-4 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
              value={String(formState.is_active)}
              onChange={(event) => setFormState((current) => ({ ...current, is_active: event.target.value === "true" }))}
            >
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </div>
          {mutation.isError ? (
            <p className="md:col-span-2 rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {extractErrorMessage(mutation.error)}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-3 md:col-span-2">
            <Button type="button" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
              {mutation.isPending ? "Saving..." : "Save changes"}
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
