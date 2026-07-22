"use client";

import { useEffect, useRef, useState, type ReactElement } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { updateRecognitionItemSelection } from "@/lib/ai";
import { createProduct } from "@/lib/products";
import { extractErrorMessage } from "@/lib/errors";

type FormState = {
  name: string;
  manufacturer: string;
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
  { id: "name", label: "Название товара", span: true },
  { id: "manufacturer", label: "Производитель", span: true },
  { id: "sku", label: "SKU" },
  { id: "barcode", label: "Штрихкод" },
  { id: "category", label: "Категория" },
  { id: "unit", label: "Единица" },
  { id: "price", label: "Цена продажи" },
  { id: "cost", label: "Себестоимость" },
  { id: "tax_rate", label: "Налог" },
];

const inventoryFields: Array<{ id: Exclude<keyof FormState, "is_active">; label: string }> = [
  { id: "stock_qty", label: "Начальный остаток" },
  { id: "low_stock_threshold", label: "Порог низкого остатка" },
];

export function NewProductPageClient(): ReactElement {
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnToRecognitionId = searchParams.get("returnToRecognitionId");
  const returnToItemIndexParam = searchParams.get("returnToItemIndex");
  const returnToItemIndex = returnToItemIndexParam ? Number(returnToItemIndexParam) : null;
  const returnToPath = searchParams.get("returnToPath");
  const finalReturnPath = returnToPath ?? (returnToRecognitionId ? `/ai/review/${returnToRecognitionId}` : null);
  const shouldLinkRecognitionItem =
    Boolean(returnToRecognitionId) && returnToItemIndex !== null && Number.isInteger(returnToItemIndex);
  const prefillName = searchParams.get("prefillName") ?? "";
  const prefilledNameRef = useRef(false);
  const [formState, setFormState] = useState<FormState>({
    name: "",
    manufacturer: "",
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
    if (prefillName && !prefilledNameRef.current) {
      setFormState((current) => ({ ...current, name: prefillName }));
      prefilledNameRef.current = true;
    }
  }, [prefillName]);

  const mutation = useMutation({
    mutationFn: async (payload: Parameters<typeof createProduct>[0]) => {
      const product = await createProduct(payload);
      if (shouldLinkRecognitionItem && returnToRecognitionId && returnToItemIndex !== null) {
        await updateRecognitionItemSelection(returnToRecognitionId, returnToItemIndex, {
          selected_product_id: product.id,
        });
      }
      return product;
    },
    onSuccess: (product) => {
      if (finalReturnPath) {
        router.push(finalReturnPath);
        return;
      }
      router.push(`/products/${product.id}`);
    },
  });

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <Badge>Редактор товара</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Создание товара</h1>
        <p className="max-w-2xl text-muted-foreground">
          Структурированный ввод товара: SKU, штрихкод, цены, категории, теги и остатки.
        </p>
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Данные товара</CardTitle>
            <CardDescription>Оптимизировано для быстрого ввода на складе или в офисе.</CardDescription>
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
            <CardTitle>Параметры склада</CardTitle>
            <CardDescription>Остаток начинается с нуля, пока не будет поступления или корректировки.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {inventoryFields.map((field) => (
              <div key={field.id} className="space-y-2">
                <Label htmlFor={field.id}>{field.label}</Label>
                <Input
                  id={field.id}
                  value={String(formState[field.id])}
                  onChange={(event) => setFormState((current) => ({ ...current, [field.id]: event.target.value }))}
                />
              </div>
            ))}
            <div className="space-y-2">
              <Label htmlFor="is_active">Статус</Label>
              <select
                id="is_active"
                className="flex h-11 w-full rounded-2xl border border-input bg-background px-4 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
                value={String(formState.is_active)}
                onChange={(event) =>
                  setFormState((current) => ({ ...current, is_active: event.target.value === "true" }))
                }
              >
                <option value="true">Активный</option>
                <option value="false">Неактивный</option>
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
                  manufacturer: formState.manufacturer.trim() || null,
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
              {mutation.isPending ? "Сохраняем..." : "Сохранить товар"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
