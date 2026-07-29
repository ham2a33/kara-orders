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
  size: string;
  price: string;
  manufacturer: string;
  category: string;
};

function buildProductName(name: string, size: string): string {
  const trimmedName = name.trim();
  const trimmedSize = size.trim();
  if (trimmedSize) {
    return `${trimmedName} - ${trimmedSize} mm`;
  }
  return trimmedName;
}

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
    size: "",
    price: "",
    manufacturer: "",
    category: "",
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

  const canSubmit = formState.name.trim().length > 0 && formState.price.trim().length > 0;
  const previewName = buildProductName(formState.name, formState.size);

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <section className="space-y-3">
        <Badge>Новый товар</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Создание товара</h1>
        <p className="text-muted-foreground">Заполните основные поля — SKU создаётся автоматически.</p>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Данные товара</CardTitle>
          <CardDescription>Название, цена и необязательные параметры.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">
              Название товара <span className="text-destructive">*</span>
            </Label>
            <Input
              id="name"
              autoFocus
              placeholder="Pipe PVC"
              value={formState.name}
              onChange={(event) => setFormState((current) => ({ ...current, name: event.target.value }))}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="size">Размер</Label>
            <div className="flex items-center gap-2">
              <Input
                id="size"
                placeholder="20"
                inputMode="decimal"
                value={formState.size}
                onChange={(event) => setFormState((current) => ({ ...current, size: event.target.value }))}
              />
              <span className="shrink-0 text-sm text-muted-foreground">mm</span>
            </div>
          </div>

          {formState.name.trim() ? (
            <p className="rounded-2xl bg-muted/60 px-4 py-2 text-sm text-muted-foreground">
              Будет сохранено как: <span className="font-medium text-foreground">{previewName}</span>
            </p>
          ) : null}

          <div className="space-y-2">
            <Label htmlFor="price">
              Цена продажи <span className="text-destructive">*</span>
            </Label>
            <Input
              id="price"
              inputMode="decimal"
              placeholder="1250"
              value={formState.price}
              onChange={(event) => setFormState((current) => ({ ...current, price: event.target.value }))}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="manufacturer">Производитель</Label>
            <Input
              id="manufacturer"
              placeholder="Необязательно"
              value={formState.manufacturer}
              onChange={(event) => setFormState((current) => ({ ...current, manufacturer: event.target.value }))}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="category">Категория</Label>
            <Input
              id="category"
              placeholder="Необязательно"
              value={formState.category}
              onChange={(event) => setFormState((current) => ({ ...current, category: event.target.value }))}
            />
          </div>

          {mutation.isError ? (
            <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {extractErrorMessage(mutation.error)}
            </p>
          ) : null}

          <Button
            className="w-full"
            type="button"
            disabled={mutation.isPending || !canSubmit}
            onClick={() =>
              mutation.mutate({
                name: buildProductName(formState.name, formState.size),
                manufacturer: formState.manufacturer.trim() || null,
                category: formState.category.trim() || null,
                price: formState.price,
                unit: "pcs",
                currency: "KZT",
                is_active: true,
              })
            }
          >
            {mutation.isPending ? "Сохраняем..." : "Сохранить товар"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
