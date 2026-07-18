"use client";

import { useState, type ReactElement } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createProduct } from "@/lib/products";
import { extractErrorMessage } from "@/lib/errors";

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

const mainFields: Array<{ id: Exclude<keyof FormState, "is_active">; label: string; span?: boolean }> = [
  { id: "name", label: "Product name", span: true },
  { id: "sku", label: "SKU" },
  { id: "barcode", label: "Barcode" },
  { id: "category", label: "Category" },
  { id: "unit", label: "Unit" },
  { id: "price", label: "Selling price" },
  { id: "cost", label: "Cost price" },
  { id: "tax_rate", label: "Tax rate" },
];

const inventoryFields: Array<{ id: Exclude<keyof FormState, "is_active">; label: string }> = [
  { id: "stock_qty", label: "Opening stock" },
  { id: "low_stock_threshold", label: "Low stock threshold" },
];

export default function NewProductPage(): ReactElement {
  const router = useRouter();
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

  const mutation = useMutation({
    mutationFn: createProduct,
    onSuccess: (product) => {
      router.push(`/products/${product.id}`);
    },
  });

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <Badge>Product editor</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Create product</h1>
        <p className="max-w-2xl text-muted-foreground">
          Structured product entry for SKU, barcode, pricing, categories, tags, and stock settings.
        </p>
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Product details</CardTitle>
            <CardDescription>Optimized for fast catalog entry in the warehouse or office.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            {mainFields.map((field) => (
              <div key={field.id} className={`space-y-2 ${field.span ? "md:col-span-2" : ""}`}>
                <Label htmlFor={field.id}>{field.label}</Label>
                <Input
                  id={field.id}
                  value={String(formState[field.id])}
                  onChange={(event) => setFormState((current) => ({ ...current, [field.id]: event.target.value }))}
                />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Inventory settings</CardTitle>
            <CardDescription>Stock starts at zero until a receipt or adjustment is recorded.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {inventoryFields.map((field) => (
              <div key={field.id} className="space-y-2">
                <Label htmlFor={field.id}>{field.label}</Label>
                <Input id={field.id} value={String(formState[field.id])} onChange={(event) => setFormState((current) => ({ ...current, [field.id]: event.target.value }))} />
              </div>
            ))}
            <div className="space-y-2">
              <Label htmlFor="is_active">Status</Label>
              <select
                id="is_active"
                className="flex h-11 w-full rounded-2xl border border-input bg-background px-4 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
                value={String(formState.is_active)}
                onChange={(event) =>
                  setFormState((current) => ({ ...current, is_active: event.target.value === "true" }))
                }
              >
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </select>
            </div>
            {mutation.isError ? (
              <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {extractErrorMessage(mutation.error)}
              </p>
            ) : null}
            <Button
              className="w-full"
              type="button"
              disabled={mutation.isPending || formState.name.trim().length === 0}
              onClick={() =>
                mutation.mutate({
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
                })
              }
            >
              {mutation.isPending ? "Saving..." : "Save product"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
