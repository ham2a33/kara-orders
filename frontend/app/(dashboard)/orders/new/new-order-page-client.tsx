"use client";

import { useEffect, useMemo, useRef, useState, type ReactElement } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Loader2, Search, Sparkles, Trash2 } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";

import { OrderCreatedDialog } from "@/components/orders/order-created-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatMoney } from "@/components/platform/shared";
import {
  confirmRecognition,
  createDraftOrderFromRecognition,
  getAIRecognition,
  updateRecognitionItemSelection,
} from "@/lib/ai";
import {
  attachProductToLine,
  buildEditableLinesFromRecognition,
  buildManualLine,
  formatLineSize,
  productSearchLabel,
  type EditableOrderLine,
} from "@/lib/ai-order-lines";
import { getMyCompany } from "@/lib/company";
import { previewOrderLine, previewOrderTotals } from "@/lib/order-line-preview";
import {
  ORDER_UNIT_OPTIONS,
  orderUnitLabel,
  quantityStepForUnit,
  type OrderUnitValue,
} from "@/lib/order-units";
import { createOrder, updateOrder } from "@/lib/orders";
import { sortProductsBySearch } from "@/lib/product-search-rank";
import { getProducts } from "@/lib/products";
import { extractErrorMessage } from "@/lib/errors";
import type { Order, OrderStatus } from "@/types/orders";
import type { Product } from "@/types/products";

type OrderLine = EditableOrderLine & {
  quantityInput: string;
  discountInput: string;
};

function toLine(line: EditableOrderLine): OrderLine {
  return {
    ...line,
    quantityInput: String(line.quantity),
    discountInput: line.discountAmount ? String(line.discountAmount) : "0",
  };
}

function parseNumberInput(raw: string): number {
  const value = Number(raw.trim().replace(",", "."));
  return Number.isFinite(value) && value > 0 ? value : 0;
}

function lineDisplayName(line: OrderLine): string {
  if (line.product) {
    return productSearchLabel(line.product);
  }
  const label = line.pendingLabel?.trim() || "Позиция без названия";
  const size = line.pendingSize?.trim();
  return size ? `${label} ${size}` : label;
}

export function NewOrderPageClient(): ReactElement {
  const router = useRouter();
  const searchParams = useSearchParams();
  const recognitionId = searchParams.get("recognitionId");
  const isAiFlow = Boolean(recognitionId);
  const hydratedFromAiRef = useRef(false);

  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<OrderStatus>("new");
  const [searchValue, setSearchValue] = useState("");
  const [clientOpen, setClientOpen] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [customerAddress, setCustomerAddress] = useState("");
  const [lines, setLines] = useState<OrderLine[]>([]);
  const [pickerLineKey, setPickerLineKey] = useState<string | null>(null);
  const [pickerSearch, setPickerSearch] = useState("");
  const [draftOrderId, setDraftOrderId] = useState<string | null>(
    searchParams.get("orderId"),
  );
  const [createdOrder, setCreatedOrder] = useState<Order | null>(null);

  const recognitionQuery = useQuery({
    queryKey: ["ai-recognition", recognitionId],
    queryFn: () => getAIRecognition(recognitionId!),
    enabled: Boolean(recognitionId),
  });

  const recognition = recognitionQuery.data;

  useEffect(() => {
    if (!recognition || hydratedFromAiRef.current) {
      return;
    }
    hydratedFromAiRef.current = true;

    if (recognition.status === "converted" && recognition.created_order_id) {
      router.replace(`/orders/${recognition.created_order_id}`);
      return;
    }

    setLines(buildEditableLinesFromRecognition(recognition).map(toLine));
    if (recognition.created_order_id) {
      setDraftOrderId(recognition.created_order_id);
    }
  }, [recognition, router]);

  const productsQuery = useQuery({
    queryKey: ["new-order-products", searchValue],
    queryFn: () =>
      getProducts({
        search: searchValue.trim() || undefined,
        pageSize: 12,
        sortBy: searchValue.trim() ? "name" : "updated_at",
        sortDir: "desc",
      }),
  });

  const companyQuery = useQuery({
    queryKey: ["company-profile"],
    queryFn: getMyCompany,
    staleTime: 5 * 60 * 1000,
  });

  /** Backend applies a single company-wide VAT rate to every line. */
  const companyTaxPercent = Number(companyQuery.data?.tax_percentage ?? 0) || 0;

  const pickerQuery = useQuery({
    queryKey: ["new-order-picker-products", pickerSearch],
    queryFn: () =>
      getProducts({
        search: pickerSearch.trim() || undefined,
        pageSize: 8,
        sortBy: pickerSearch.trim() ? "name" : "updated_at",
        sortDir: "desc",
      }),
    enabled: Boolean(pickerLineKey),
  });

  const searchResults = useMemo(
    () =>
      sortProductsBySearch(productsQuery.data?.items ?? [], searchValue).slice(
        0,
        8,
      ),
    [productsQuery.data?.items, searchValue],
  );

  const addProduct = (product: Product): void => {
    setLines((current) => {
      const existing = current.find(
        (line) => line.product?.id === product.id && line.aiItemIndex === null,
      );
      if (existing) {
        const nextQuantity = parseNumberInput(existing.quantityInput) + 1;
        return current.map((line) =>
          line === existing
            ? {
                ...line,
                quantity: nextQuantity,
                quantityInput: String(nextQuantity),
              }
            : line,
        );
      }
      return [
        ...current,
        toLine(buildManualLine(product, `manual-${product.id}-${Date.now()}`)),
      ];
    });
    setSearchValue("");
    searchInputRef.current?.focus();
  };

  const updateLine = (key: string, patch: Partial<OrderLine>): void => {
    setLines((current) =>
      current.map((line) => (line.key === key ? { ...line, ...patch } : line)),
    );
  };

  const removeLine = (key: string): void => {
    setLines((current) => current.filter((line) => line.key !== key));
    if (pickerLineKey === key) {
      setPickerLineKey(null);
    }
  };

  const selectProductForLine = (line: OrderLine, product: Product): void => {
    setLines((current) =>
      current.map((entry) =>
        entry.key === line.key
          ? {
              ...toLine(attachProductToLine(entry, product)),
              quantityInput: entry.quantityInput,
              discountInput: entry.discountInput,
            }
          : entry,
      ),
    );
    setPickerLineKey(null);
    setPickerSearch("");

    if (recognitionId && line.aiItemIndex !== null) {
      // Teaches the matcher which catalog product belongs to this recognized line.
      void updateRecognitionItemSelection(recognitionId, line.aiItemIndex, {
        selected_product_id: product.id,
      }).catch(() => undefined);
    }
  };

  const linePreviews = useMemo(
    () =>
      lines.map((line) =>
        previewOrderLine({
          quantity: parseNumberInput(line.quantityInput),
          unitPrice: line.unitPrice,
          discountAmount: parseNumberInput(line.discountInput),
          taxPercent: companyTaxPercent,
        }),
      ),
    [companyTaxPercent, lines],
  );

  const totals = useMemo(
    () => previewOrderTotals(linePreviews),
    [linePreviews],
  );

  const unresolvedCount = lines.filter((line) => line.product === null).length;
  const invalidQuantityCount = lines.filter(
    (line) => parseNumberInput(line.quantityInput) <= 0,
  ).length;
  const invalidDiscountCount = lines.filter(
    (line) =>
      parseNumberInput(line.discountInput) >
      parseNumberInput(line.quantityInput) * line.unitPrice,
  ).length;

  const buildPayload = () => ({
    customer_name: customerName.trim() || null,
    customer_phone: customerPhone.trim() || null,
    customer_address: customerAddress.trim() || null,
    notes: notes.trim() || null,
    items: lines
      .filter((line) => line.product !== null)
      .map((line) => ({
        product_id: line.product!.id,
        quantity: parseNumberInput(line.quantityInput),
        discount_amount: parseNumberInput(line.discountInput),
      })),
  });

  const saveDraftMutation = useMutation({
    mutationFn: async () => {
      const payload = { ...buildPayload(), status: "draft" as const };
      if (draftOrderId) {
        return updateOrder(draftOrderId, payload);
      }
      if (recognitionId) {
        const linked = await createDraftOrderFromRecognition(
          recognitionId,
        ).catch(() => null);
        if (linked) {
          return updateOrder(linked.order.id, payload);
        }
      }
      return createOrder(payload);
    },
    onSuccess: (order) => {
      setDraftOrderId(order.id);
    },
  });

  const submitMutation = useMutation({
    mutationFn: async () => {
      const payload = buildPayload();
      if (recognitionId) {
        const response = await confirmRecognition(recognitionId, {
          ...payload,
          status: "new",
        });
        return response.order as unknown as Order;
      }
      return createOrder({ ...payload, status });
    },
    onSuccess: (order) => {
      setCreatedOrder(order);
    },
  });

  const isBusy = submitMutation.isPending || saveDraftMutation.isPending;
  const isValid = invalidQuantityCount === 0 && invalidDiscountCount === 0;
  const canSubmit =
    lines.length > 0 && unresolvedCount === 0 && isValid && !isBusy;
  const canSaveDraft =
    lines.some((line) => line.product !== null) && isValid && !isBusy;

  if (isAiFlow && recognitionQuery.isLoading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-muted-foreground">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        Загружаем распознанные позиции…
      </div>
    );
  }

  if (isAiFlow && recognitionQuery.isError) {
    return (
      <Card className="max-w-xl">
        <CardContent className="space-y-4 p-6">
          <p className="text-sm text-destructive">
            {extractErrorMessage(recognitionQuery.error)}
          </p>
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push("/orders/new")}
          >
            Создать заказ вручную
          </Button>
        </CardContent>
      </Card>
    );
  }

  const renderPicker = (line: OrderLine): ReactElement => {
    const candidates = line.candidates;
    const catalogResults = sortProductsBySearch(
      pickerQuery.data?.items ?? [],
      pickerSearch,
    ).slice(0, 6);
    const options = pickerSearch.trim()
      ? catalogResults
      : [...candidates, ...catalogResults];
    const seen = new Set<string>();
    const uniqueOptions = options.filter((product) => {
      if (seen.has(product.id)) {
        return false;
      }
      seen.add(product.id);
      return true;
    });

    return (
      <div className="mt-3 space-y-3 rounded-2xl border bg-muted/30 p-3">
        <Input
          autoFocus
          value={pickerSearch}
          onChange={(event) => setPickerSearch(event.target.value)}
          placeholder="Поиск по каталогу: название, SKU, штрихкод…"
          className="h-11 rounded-xl"
        />
        <div className="space-y-2">
          {pickerQuery.isFetching ? (
            <p className="text-xs text-muted-foreground">Загрузка…</p>
          ) : null}
          {uniqueOptions.map((product) => (
            <button
              key={product.id}
              type="button"
              onClick={() => selectProductForLine(line, product)}
              className="flex w-full items-center justify-between gap-3 rounded-xl border bg-background px-3 py-2 text-left text-sm transition-colors hover:bg-muted"
            >
              <span className="min-w-0">
                <span className="block truncate font-medium">
                  {productSearchLabel(product)}
                </span>
                <span className="block truncate text-xs text-muted-foreground">
                  {product.manufacturer ?? "Без производителя"} · SKU:{" "}
                  {product.sku ?? "—"}
                </span>
              </span>
              <span className="whitespace-nowrap text-xs font-semibold">
                {formatMoney(product.price, product.currency)}
              </span>
            </button>
          ))}
          {!pickerQuery.isFetching && uniqueOptions.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              Ничего не найдено. Уточните запрос или добавьте товар в каталог.
            </p>
          ) : null}
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setPickerLineKey(null)}
        >
          Отмена
        </Button>
      </div>
    );
  };

  return (
    <div className="flex flex-col gap-6 pb-40">
      {createdOrder ? (
        <OrderCreatedDialog
          order={createdOrder}
          open={Boolean(createdOrder)}
          onClose={() => {
            const orderId = createdOrder.id;
            setCreatedOrder(null);
            router.push(`/orders/${orderId}`);
          }}
        />
      ) : null}

      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
            Касса
          </p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Новый заказ
          </h1>
          {isAiFlow ? (
            <Badge className="gap-1">
              <Sparkles className="h-3.5 w-3.5" />
              Позиции подставлены ИИ — проверьте и отредактируйте
            </Badge>
          ) : null}
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <div className="w-full max-w-xs space-y-1">
            <Label
              htmlFor="order-notes"
              className="text-xs text-muted-foreground"
            >
              Комментарий
            </Label>
            <Input
              id="order-notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Комментарий (необяз.)"
              className="h-11 rounded-2xl"
            />
          </div>
          {!isAiFlow ? (
            <div className="space-y-1">
              <Label
                htmlFor="order-status"
                className="text-xs text-muted-foreground"
              >
                Статус
              </Label>
              <select
                id="order-status"
                className="flex h-11 rounded-2xl border border-input bg-background px-4 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={status}
                onChange={(event) =>
                  setStatus(event.target.value as OrderStatus)
                }
              >
                <option value="new">Новый</option>
                <option value="confirmed">Подтвержден</option>
              </select>
            </div>
          ) : null}
          <Button
            type="button"
            variant="outline"
            className="h-11"
            onClick={() => setClientOpen((current) => !current)}
          >
            {clientOpen ? "Скрыть клиента" : "Клиент"}
          </Button>
        </div>
      </section>

      {clientOpen ? (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Клиент</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="customer-name">Имя</Label>
              <Input
                id="customer-name"
                value={customerName}
                onChange={(event) => setCustomerName(event.target.value)}
                placeholder="Имя клиента"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="customer-phone">Телефон</Label>
              <Input
                id="customer-phone"
                value={customerPhone}
                onChange={(event) => setCustomerPhone(event.target.value)}
                placeholder="+7 ..."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="customer-address">Адрес</Label>
              <Input
                id="customer-address"
                value={customerAddress}
                onChange={(event) => setCustomerAddress(event.target.value)}
                placeholder="Адрес доставки"
              />
            </div>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-6">
          <Card className="shadow-soft">
            <CardContent className="space-y-2 p-4 sm:p-5">
              <div className="relative">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  ref={searchInputRef}
                  value={searchValue}
                  onChange={(event) => setSearchValue(event.target.value)}
                  placeholder="Поиск: название, SKU, штрихкод…"
                  className="h-14 rounded-2xl pl-11 text-base"
                />
              </div>
              <p className="px-1 text-xs text-muted-foreground">
                Введите запрос — товар добавится в заказ сразу после выбора.
              </p>

              {searchValue.trim() ? (
                <div className="space-y-2 pt-1">
                  {productsQuery.isFetching ? (
                    <p className="px-1 text-xs text-muted-foreground">
                      Загрузка…
                    </p>
                  ) : null}
                  {searchResults.map((product) => (
                    <button
                      key={product.id}
                      type="button"
                      onClick={() => addProduct(product)}
                      className="flex w-full items-center justify-between gap-3 rounded-2xl border bg-background px-4 py-3 text-left transition-colors hover:bg-muted"
                    >
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-medium">
                          {productSearchLabel(product)}
                        </span>
                        <span className="block truncate text-xs text-muted-foreground">
                          {product.manufacturer ?? "Без производителя"} ·
                          Остаток: {product.stock_qty ?? "0"}
                        </span>
                      </span>
                      <span className="whitespace-nowrap text-sm font-semibold">
                        {formatMoney(product.price, product.currency)}
                      </span>
                    </button>
                  ))}
                  {!productsQuery.isFetching && searchResults.length === 0 ? (
                    <p className="px-1 text-xs text-muted-foreground">
                      Ничего не найдено. Проверьте название, SKU, штрихкод или
                      alias.
                    </p>
                  ) : null}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card className="shadow-soft">
            <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-base">Позиции заказа</CardTitle>
              <p className="text-xs text-muted-foreground">
                {lines.length} поз.
              </p>
            </CardHeader>
            <CardContent className="p-0">
              {lines.length === 0 ? (
                <p className="p-6 text-sm text-muted-foreground">
                  Добавьте товары через поиск, чтобы собрать заказ.
                </p>
              ) : (
                <div className="divide-y">
                  <div className="hidden grid-cols-[minmax(0,2.2fr)_90px_80px_minmax(0,1fr)_90px_minmax(0,1fr)_minmax(0,1fr)_40px] gap-3 px-5 py-3 text-[11px] font-medium uppercase tracking-wide text-muted-foreground lg:grid">
                    <span>Товар</span>
                    <span>Кол-во</span>
                    <span>Ед.</span>
                    <span>Цена</span>
                    <span>Скидка</span>
                    <span>НДС</span>
                    <span>Сумма</span>
                    <span />
                  </div>

                  {lines.map((line, index) => {
                    const preview = linePreviews[index];
                    const currency = line.product?.currency ?? "KZT";
                    const isPickerOpen = pickerLineKey === line.key;

                    return (
                      <div key={line.key} className="px-4 py-4 sm:px-5">
                        <div className="grid gap-3 lg:grid-cols-[minmax(0,2.2fr)_90px_80px_minmax(0,1fr)_90px_minmax(0,1fr)_minmax(0,1fr)_40px] lg:items-center">
                          <div className="min-w-0 space-y-1">
                            <p className="truncate text-sm font-semibold">
                              {lineDisplayName(line)}
                            </p>
                            <p className="truncate text-xs text-muted-foreground">
                              {line.product
                                ? (line.product.manufacturer ??
                                  "Без производителя")
                                : "Товар не выбран"}
                              {line.product || line.pendingSize
                                ? ` · ${formatLineSize(line.product, line.pendingSize)}`
                                : ""}
                            </p>
                            <Button
                              type="button"
                              size="sm"
                              variant={line.product ? "ghost" : "outline"}
                              className={
                                line.product ? "h-7 px-2 text-xs" : undefined
                              }
                              onClick={() => {
                                setPickerLineKey(
                                  isPickerOpen ? null : line.key,
                                );
                                setPickerSearch("");
                              }}
                            >
                              {isPickerOpen
                                ? "Закрыть выбор"
                                : line.product
                                  ? "Заменить товар"
                                  : "Выбрать товар"}
                            </Button>
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground lg:hidden">
                              Кол-во
                            </span>
                            <Input
                              inputMode="decimal"
                              step={quantityStepForUnit(line.unit)}
                              value={line.quantityInput}
                              onChange={(event) =>
                                updateLine(line.key, {
                                  quantityInput: event.target.value,
                                })
                              }
                              className="h-10 w-full rounded-xl text-center"
                              aria-label={`Количество: ${lineDisplayName(line)}`}
                            />
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground lg:hidden">
                              Ед.
                            </span>
                            <select
                              value={line.unit}
                              onChange={(event) =>
                                updateLine(line.key, {
                                  unit: event.target.value as OrderUnitValue,
                                })
                              }
                              className="h-10 w-full rounded-xl border border-input bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                              aria-label={`Единица измерения: ${lineDisplayName(line)}`}
                            >
                              {ORDER_UNIT_OPTIONS.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                          </div>

                          <div className="text-sm text-muted-foreground">
                            <span className="lg:hidden">Цена: </span>
                            {line.product
                              ? `${formatMoney(String(line.unitPrice), currency)} / ${orderUnitLabel(line.unit)}`
                              : "—"}
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground lg:hidden">
                              Скидка
                            </span>
                            <Input
                              inputMode="decimal"
                              value={line.discountInput}
                              onChange={(event) =>
                                updateLine(line.key, {
                                  discountInput: event.target.value,
                                })
                              }
                              className="h-10 w-full rounded-xl text-center"
                              aria-label={`Скидка: ${lineDisplayName(line)}`}
                            />
                          </div>

                          <div className="text-sm text-muted-foreground">
                            <span className="lg:hidden">НДС: </span>
                            {formatMoney(
                              preview.taxAmount.toFixed(2),
                              currency,
                            )}
                          </div>

                          <div className="text-sm font-semibold">
                            <span className="text-xs font-normal text-muted-foreground lg:hidden">
                              Сумма:{" "}
                            </span>
                            {formatMoney(
                              preview.lineTotal.toFixed(2),
                              currency,
                            )}
                          </div>

                          <div className="flex justify-end">
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => removeLine(line.key)}
                              aria-label={`Удалить: ${lineDisplayName(line)}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>

                        {isPickerOpen ? renderPicker(line) : null}
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <aside className="hidden lg:block">
          <Card className="sticky top-24 shadow-soft">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Итоги</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <dl className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <dt className="text-muted-foreground">Подытог</dt>
                  <dd>{formatMoney(totals.subtotal.toFixed(2))}</dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-muted-foreground">Скидка</dt>
                  <dd>{formatMoney(totals.discountTotal.toFixed(2))}</dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-muted-foreground">НДС</dt>
                  <dd>{formatMoney(totals.taxTotal.toFixed(2))}</dd>
                </div>
                <div className="flex items-center justify-between border-t pt-3 text-base font-semibold">
                  <dt>Итого</dt>
                  <dd>{formatMoney(totals.total.toFixed(2))}</dd>
                </div>
              </dl>

              {unresolvedCount > 0 ? (
                <p className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs text-amber-700 dark:text-amber-300">
                  Выберите товар для {unresolvedCount} поз. — без этого заказ
                  создать нельзя.
                </p>
              ) : null}
              {invalidQuantityCount > 0 ? (
                <p className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs text-amber-700 dark:text-amber-300">
                  Укажите количество больше нуля в {invalidQuantityCount} поз.
                </p>
              ) : null}
              {invalidDiscountCount > 0 ? (
                <p className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs text-amber-700 dark:text-amber-300">
                  Скидка не может превышать стоимость позиции (
                  {invalidDiscountCount} поз.).
                </p>
              ) : null}

              <Button
                type="button"
                className="w-full"
                disabled={!canSubmit}
                onClick={() => submitMutation.mutate()}
              >
                {submitMutation.isPending ? "Создаём заказ…" : "Создать заказ"}
              </Button>
              <Button
                type="button"
                variant="outline"
                className="w-full"
                disabled={!canSaveDraft}
                onClick={() => saveDraftMutation.mutate()}
              >
                {saveDraftMutation.isPending
                  ? "Сохраняем…"
                  : "Сохранить черновик"}
              </Button>

              {submitMutation.isError || saveDraftMutation.isError ? (
                <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {extractErrorMessage(
                    submitMutation.error ?? saveDraftMutation.error,
                  )}
                </p>
              ) : null}
            </CardContent>
          </Card>
        </aside>
      </div>

      <div className="fixed inset-x-4 bottom-20 z-30 lg:hidden">
        <Card className="shadow-soft">
          <CardContent className="space-y-3 p-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Итого</span>
              <span className="text-lg font-semibold">
                {formatMoney(totals.total.toFixed(2))}
              </span>
            </div>
            {unresolvedCount > 0 ? (
              <p className="text-xs text-amber-600 dark:text-amber-400">
                Выберите товар для {unresolvedCount} поз.
              </p>
            ) : null}
            <Button
              type="button"
              className="w-full"
              disabled={!canSubmit}
              onClick={() => submitMutation.mutate()}
            >
              {submitMutation.isPending ? "Создаём заказ…" : "Создать заказ"}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="w-full"
              disabled={!canSaveDraft}
              onClick={() => saveDraftMutation.mutate()}
            >
              {saveDraftMutation.isPending
                ? "Сохраняем…"
                : "Сохранить черновик"}
            </Button>
            {submitMutation.isError || saveDraftMutation.isError ? (
              <p className="text-xs text-destructive">
                {extractErrorMessage(
                  submitMutation.error ?? saveDraftMutation.error,
                )}
              </p>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
