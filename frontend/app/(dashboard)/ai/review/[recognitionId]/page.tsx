"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { confirmRecognition, getAIRecognition, updateRecognitionItemSelection } from "@/lib/ai";
import { extractErrorMessage } from "@/lib/errors";
import { formatMoney } from "@/components/platform/shared";
import type { AIRecognition, AIRecognitionItem } from "@/types/ai";

type FormState = {
  customerName: string;
  customerPhone: string;
  customerAddress: string;
  notes: string;
};

function buildSelectionMap(recognition: AIRecognition | undefined): Record<number, string> {
  if (!recognition) {
    return {};
  }
  return recognition.items.reduce<Record<number, string>>((accumulator, item, index) => {
    const fallbackSelected =
      item.selected_product_id ??
      item.matched_product?.id ??
      (item.candidate_products.length === 1 ? item.candidate_products[0]?.id ?? null : null);
    if (fallbackSelected) {
      accumulator[index] = fallbackSelected;
    }
    return accumulator;
  }, {});
}

function resolveSelectedProductId(item: AIRecognitionItem, index: number, selectedProductIds: Record<number, string>): string | null {
  return (
    selectedProductIds[index] ??
    item.selected_product_id ??
    item.matched_product?.id ??
    (item.candidate_products.length === 1 ? item.candidate_products[0]?.id ?? null : null)
  );
}

function candidateLabel(candidate: AIRecognitionItem["candidate_products"][number]): string {
  return candidate.manufacturer?.trim() || candidate.name;
}

export default function AiReviewPage(): ReactElement {
  const params = useParams<{ recognitionId: string }>();
  const recognitionId = params.recognitionId;
  const router = useRouter();
  const queryClient = useQueryClient();

  const [formState, setFormState] = useState<FormState>({
    customerName: "",
    customerPhone: "",
    customerAddress: "",
    notes: "",
  });
  const [selectedProductIds, setSelectedProductIds] = useState<Record<number, string>>({});

  const query = useQuery({
    queryKey: ["ai-recognition", recognitionId],
    queryFn: () => getAIRecognition(recognitionId),
    enabled: Boolean(recognitionId),
  });

  useEffect(() => {
    setSelectedProductIds(buildSelectionMap(query.data));
  }, [query.data]);

  const items = query.data?.items ?? [];
  const hasUnresolvedItems = useMemo(
    () => items.some((item, index) => resolveSelectedProductId(item, index, selectedProductIds) === null),
    [items, selectedProductIds],
  );

  const selectionMutation = useMutation({
    mutationFn: ({ itemIndex, selectedProductId }: { itemIndex: number; selectedProductId: string }) =>
      updateRecognitionItemSelection(recognitionId, itemIndex, { selected_product_id: selectedProductId }),
    onSuccess: async (recognition) => {
      queryClient.setQueryData(["ai-recognition", recognitionId], recognition);
      setSelectedProductIds(buildSelectionMap(recognition));
      await queryClient.invalidateQueries({ queryKey: ["ai-history"] });
    },
    onError: () => {
      setSelectedProductIds(buildSelectionMap(query.data));
    },
  });

  const confirmMutation = useMutation({
    mutationFn: () =>
      confirmRecognition(recognitionId, {
        customer_name: formState.customerName.trim() || null,
        customer_phone: formState.customerPhone.trim() || null,
        customer_address: formState.customerAddress.trim() || null,
        notes: formState.notes.trim() || null,
        status: "draft",
        items: items.map((item, index) => {
          const selectedProductId = resolveSelectedProductId(item, index, selectedProductIds);
          if (!selectedProductId) {
            throw new Error("Выберите товар для всех позиций.");
          }
          return {
            product_id: selectedProductId,
            quantity: item.quantity,
            discount_amount: "0",
          };
        }),
      }),
    onSuccess: async (response) => {
      await queryClient.invalidateQueries({ queryKey: ["ai-history"] });
      router.push(`/orders/${response.order.id}`);
    },
  });

  const createProductHref = (item: AIRecognitionItem, index: number): string => {
    const searchParams = new URLSearchParams({
      prefillName: item.recognized_name,
      returnToRecognitionId: recognitionId,
      returnToItemIndex: String(index),
      returnToPath: `/ai/review/${recognitionId}`,
    });
    return `/products/new?${searchParams.toString()}`;
  };

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <Badge>Проверка AI-заказа</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Проверка распознавания {recognitionId}</h1>
        <p className="max-w-2xl text-muted-foreground">
          Когда AI не может однозначно выбрать товар, мы не гадаем. Выберите позицию вручную и только затем создавайте заказ.
        </p>
      </section>

      {query.isError ? (
        <Card className="border-destructive/30">
          <CardContent className="p-5 text-sm text-destructive">{extractErrorMessage(query.error)}</CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.85fr]">
        <Card>
          <CardHeader>
            <CardTitle>Позиции распознавания</CardTitle>
            <CardDescription>Селектор появляется только там, где есть неоднозначность каталога.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {items.map((item, index) => {
              const selectedProductId = resolveSelectedProductId(item, index, selectedProductIds);
              const candidateCount = item.candidate_products.length;
              const isResolved = Boolean(selectedProductId);
              const isExactMatch = candidateCount === 1;
              const isUnresolvedMultiple = candidateCount > 1 && !isResolved;
              const isNotFound = candidateCount === 0;
              const selectedCandidate =
                item.candidate_products.find((candidate) => candidate.id === selectedProductId) ??
                (candidateCount === 1 ? item.candidate_products[0] ?? null : null);

              return (
                <div key={`${item.recognized_name}-${index}`} className="rounded-3xl border bg-card p-4 md:p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-1">
                      <p className="text-lg font-medium">{item.recognized_name}</p>
                      <p className="text-sm text-muted-foreground">Количество: {item.quantity}</p>
                    </div>
                    <Badge variant={isNotFound ? "danger" : isUnresolvedMultiple ? "warning" : "success"}>
                      {isNotFound ? "Товар не найден" : isUnresolvedMultiple ? "Требует выбора" : "Готово"}
                    </Badge>
                  </div>

                  {isNotFound ? (
                    <div className="mt-4 rounded-2xl border border-dashed bg-muted/20 p-4">
                      <p className="font-medium">⚠️ Товар не найден.</p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        Добавьте товар в каталог, затем мы автоматически привяжем его к этой позиции.
                      </p>
                      <Button asChild className="mt-4">
                        <Link href={createProductHref(item, index)}>Создать товар</Link>
                      </Button>
                    </div>
                  ) : null}

                  {isExactMatch && selectedCandidate ? (
                    <div className="mt-4 rounded-2xl border bg-muted/20 p-4">
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <p className="font-medium">{candidateLabel(selectedCandidate)}</p>
                          <p className="text-sm text-muted-foreground">{selectedCandidate.name}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">{formatMoney(selectedCandidate.price)}</p>
                          <p className="text-sm text-muted-foreground">
                            Остаток: {selectedCandidate.stock_quantity ?? "0"}
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : null}

                  {candidateCount > 1 ? (
                    <div className="mt-4 space-y-3">
                      <p className="text-sm font-medium">Выберите товар:</p>
                      <div className="divide-y overflow-hidden rounded-2xl border">
                        {item.candidate_products.map((candidate) => {
                          const checked = selectedProductId === candidate.id;
                          return (
                            <label
                              key={candidate.id}
                              className="flex min-h-12 cursor-pointer items-center gap-3 bg-background px-4 py-3 transition-colors hover:bg-muted/40"
                            >
                              <input
                                type="radio"
                                name={`recognition-item-${index}`}
                                className="h-4 w-4 shrink-0"
                                checked={checked}
                                onChange={() => {
                                  setSelectedProductIds((current) => ({ ...current, [index]: candidate.id }));
                                  selectionMutation.mutate({ itemIndex: index, selectedProductId: candidate.id });
                                }}
                              />
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center justify-between gap-4">
                                  <div className="min-w-0">
                                    <p className="font-medium">{candidateLabel(candidate)}</p>
                                    <p className="truncate text-xs text-muted-foreground">
                                      {candidate.name}
                                      {candidate.sku ? ` • SKU ${candidate.sku}` : ""}
                                    </p>
                                  </div>
                                  <div className="shrink-0 text-right">
                                    <p className="font-medium">{formatMoney(candidate.price)}</p>
                                    <p className="text-xs text-muted-foreground">
                                      Остаток: {candidate.stock_quantity ?? "0"}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            </label>
                          );
                        })}
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Создать заказ</CardTitle>
            <CardDescription>Подтвердите данные клиента и создайте заказ только после выбора всех товаров.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="customerName">Имя клиента</Label>
              <Input
                id="customerName"
                value={formState.customerName}
                onChange={(event) => setFormState((current) => ({ ...current, customerName: event.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="customerPhone">Телефон</Label>
              <Input
                id="customerPhone"
                value={formState.customerPhone}
                onChange={(event) => setFormState((current) => ({ ...current, customerPhone: event.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="customerAddress">Адрес</Label>
              <Input
                id="customerAddress"
                value={formState.customerAddress}
                onChange={(event) => setFormState((current) => ({ ...current, customerAddress: event.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="notes">Комментарий</Label>
              <Input
                id="notes"
                value={formState.notes}
                onChange={(event) => setFormState((current) => ({ ...current, notes: event.target.value }))}
              />
            </div>

            {hasUnresolvedItems ? (
              <p className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-300">
                Выберите товар для всех позиций.
              </p>
            ) : null}

            {(confirmMutation.isError || selectionMutation.isError) ? (
              <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {extractErrorMessage(confirmMutation.error ?? selectionMutation.error)}
              </p>
            ) : null}

            <Button
              className="w-full"
              type="button"
              disabled={confirmMutation.isPending || hasUnresolvedItems || items.length === 0}
              onClick={() => confirmMutation.mutate()}
            >
              {confirmMutation.isPending ? "Создаём заказ..." : "Создать заказ"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
