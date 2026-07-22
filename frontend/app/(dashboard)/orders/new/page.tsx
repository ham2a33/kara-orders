"use client";

import Link from "next/link";
import { useMemo, useRef, useState, type ReactElement } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Eye, Minus, PackageSearch, Plus, Search, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatCount, formatMoney } from "@/components/platform/shared";
import { createOrder } from "@/lib/orders";
import { getProducts } from "@/lib/products";
import { extractErrorMessage } from "@/lib/errors";
import type { Product } from "@/types/products";

type OrderLine = {
  product: Product;
  quantity: number;
};

function normalizeText(value: string): string {
  return value.trim().toLowerCase();
}

function productMatchesSearch(product: Product, searchValue: string): boolean {
  if (!searchValue) {
    return true;
  }

  const terms = [
    product.name,
    product.manufacturer ?? "",
    product.sku ?? "",
    product.barcode ?? "",
    product.category ?? "",
    product.aliases.join(" "),
  ]
    .join(" ")
    .toLowerCase();

  return terms.includes(searchValue);
}

function lineTotal(line: OrderLine): number {
  return Number(line.product.price || 0) * line.quantity;
}

export default function NewOrderPage(): ReactElement {
  const router = useRouter();
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const [orderTitle, setOrderTitle] = useState("");
  const [searchValue, setSearchValue] = useState("");
  const [clientOpen, setClientOpen] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [customerAddress, setCustomerAddress] = useState("");
  const [items, setItems] = useState<OrderLine[]>([]);

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

  const addProduct = (product: Product): void => {
    setItems((current) => {
      const existing = current.find((item) => item.product.id === product.id);
      if (existing) {
        return current.map((item) =>
          item.product.id === product.id ? { ...item, quantity: item.quantity + 1 } : item,
        );
      }
      return [...current, { product, quantity: 1 }];
    });
    setSearchValue("");
    searchInputRef.current?.focus();
  };

  const changeQuantity = (productId: string, delta: number): void => {
    setItems((current) =>
      current
        .map((item) => {
          if (item.product.id !== productId) {
            return item;
          }
          return { ...item, quantity: item.quantity + delta };
        })
        .filter((item) => item.quantity > 0),
    );
  };

  const removeProduct = (productId: string): void => {
    setItems((current) => current.filter((item) => item.product.id !== productId));
  };

  const mutation = useMutation({
    mutationFn: createOrder,
    onSuccess: (order) => {
      router.push(`/orders/${order.id}`);
    },
  });

  const products = productsQuery.data?.items;
  const visibleProducts = useMemo(() => {
    const search = normalizeText(searchValue);
    return (products ?? []).filter((product) => productMatchesSearch(product, search));
  }, [products, searchValue]);

  const subtotal = useMemo(
    () => items.reduce((total, item) => total + lineTotal(item), 0),
    [items],
  );
  const totalQuantity = useMemo(
    () => items.reduce((total, item) => total + item.quantity, 0),
    [items],
  );
  const totalItems = items.length;
  const canSubmit = items.length > 0 && !mutation.isPending;

  return (
    <div className="flex flex-col gap-6 pb-40">
      <section className="space-y-4">
        <div className="space-y-3">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">Новый заказ №000000</h1>
          <div className="max-w-xl">
            <Label htmlFor="order-title" className="sr-only">
              Название заказа
            </Label>
            <Input
              id="order-title"
              value={orderTitle}
              onChange={(event) => setOrderTitle(event.target.value)}
              placeholder="Название заказа (необязательно)"
              className="h-12 rounded-2xl"
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button type="button" variant="outline" size="sm" onClick={() => setClientOpen((current) => !current)}>
            {clientOpen ? "Скрыть клиента" : "Добавить клиента"}
          </Button>
        </div>

        {clientOpen ? (
          <Card className="max-w-3xl">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Клиент</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
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
              <div className="space-y-2 md:col-span-2">
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
      </section>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <Card className="shadow-soft">
            <CardHeader className="space-y-2">
              <CardTitle className="text-base">Поиск товара</CardTitle>
              <p className="text-sm text-muted-foreground">
                Ищите по названию, производителю, SKU, штрихкоду и alias. Выбор сразу добавляет товар в заказ.
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="relative">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  ref={searchInputRef}
                  value={searchValue}
                  onChange={(event) => setSearchValue(event.target.value)}
                  placeholder="Поиск товара..."
                  className="h-14 rounded-2xl pl-11 text-base"
                />
              </div>

              <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
                <span>
                  {searchValue.trim()
                    ? `Найдено ${formatCount(visibleProducts.length)}`
                    : "Показаны последние товары для быстрого выбора"}
                </span>
                {productsQuery.isFetching ? <span>Загрузка…</span> : null}
              </div>

              <div className="grid gap-3">
                {visibleProducts.map((product) => {
                  const stock = Number(product.stock_qty ?? 0);
                  return (
                    <Card key={product.id} className="overflow-hidden border shadow-sm transition-shadow hover:shadow-md">
                      <CardContent className="space-y-4 p-4 sm:p-5">
                        <div className="flex items-start justify-between gap-4">
                          <div className="space-y-1">
                            <p className="text-base font-semibold tracking-tight">{product.name}</p>
                            <p className="text-sm text-muted-foreground">{product.manufacturer ?? "Без производителя"}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-semibold">{formatMoney(product.price, product.currency)}</p>
                            <p className="text-xs text-muted-foreground">Остаток: {formatCount(stock)}</p>
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                          <span className="rounded-full bg-muted px-3 py-1">SKU: {product.sku ?? "—"}</span>
                          <span className="rounded-full bg-muted px-3 py-1">Штрихкод: {product.barcode ?? "—"}</span>
                        </div>

                        <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
                          <Button type="button" variant="outline" size="sm" asChild>
                            <Link href={`/products/${product.id}`}>
                              <Eye className="h-4 w-4" />
                              Подробнее
                            </Link>
                          </Button>
                          <Button type="button" size="sm" onClick={() => addProduct(product)}>
                            <PackageSearch className="h-4 w-4" />
                            Добавить
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}

                {productsQuery.isLoading ? (
                  <Card className="border-dashed">
                    <CardContent className="p-6 text-sm text-muted-foreground">Загружаем товары…</CardContent>
                  </Card>
                ) : visibleProducts.length === 0 ? (
                  <Card className="border-dashed">
                    <CardContent className="p-6 text-sm text-muted-foreground">
                      Ничего не найдено. Попробуйте другой запрос или проверьте название, SKU, штрихкод и alias.
                    </CardContent>
                  </Card>
                ) : null}
              </div>
            </CardContent>
          </Card>

          <section className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold tracking-tight">Товары в заказе</h2>
              <p className="text-sm text-muted-foreground">{formatCount(items.length)} позиций</p>
            </div>

            <div className="grid gap-3">
              {items.length > 0 ? (
                items.map((item) => {
                  const total = lineTotal(item);
                  const stock = Number(item.product.stock_qty ?? 0);
                  return (
                    <Card key={item.product.id} className="overflow-hidden shadow-soft">
                      <CardContent className="space-y-4 p-4 sm:p-5">
                        <div className="flex items-start justify-between gap-4">
                          <div className="space-y-1">
                            <p className="text-base font-semibold tracking-tight">{item.product.name}</p>
                            <p className="text-sm text-muted-foreground">{item.product.manufacturer ?? "Без производителя"}</p>
                          </div>
                          <Button type="button" variant="ghost" size="sm" onClick={() => removeProduct(item.product.id)}>
                            <Trash2 className="h-4 w-4" />
                            Удалить
                          </Button>
                        </div>

                        <div className="grid gap-3 text-sm sm:grid-cols-3">
                          <div className="rounded-2xl bg-muted/50 p-3">
                            <p className="text-xs text-muted-foreground">Цена</p>
                            <p className="mt-1 font-medium">{formatMoney(item.product.price, item.product.currency)}</p>
                          </div>
                          <div className="rounded-2xl bg-muted/50 p-3">
                            <p className="text-xs text-muted-foreground">Остаток</p>
                            <p className="mt-1 font-medium">{formatCount(stock)}</p>
                          </div>
                          <div className="rounded-2xl bg-muted/50 p-3">
                            <p className="text-xs text-muted-foreground">Стоимость</p>
                            <p className="mt-1 font-medium">{formatMoney(total.toFixed(2), item.product.currency)}</p>
                          </div>
                        </div>

                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-muted-foreground">Количество</span>
                            <Button type="button" variant="outline" size="sm" onClick={() => changeQuantity(item.product.id, -1)}>
                              <Minus className="h-4 w-4" />
                            </Button>
                            <div className="min-w-12 rounded-xl border bg-background px-3 py-2 text-center text-sm font-semibold">
                              {item.quantity}
                            </div>
                            <Button type="button" variant="outline" size="sm" onClick={() => changeQuantity(item.product.id, 1)}>
                              <Plus className="h-4 w-4" />
                            </Button>
                          </div>

                          <Button type="button" variant="outline" size="sm" asChild className="w-fit">
                            <Link href={`/products/${item.product.id}`}>
                              <Eye className="h-4 w-4" />
                              Открыть карточку товара
                            </Link>
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              ) : (
                <Card className="border-dashed">
                  <CardContent className="p-6 text-sm text-muted-foreground">
                    Добавьте товары из поиска, чтобы собрать заказ.
                  </CardContent>
                </Card>
              )}
            </div>
          </section>
        </div>

        <aside className="hidden lg:block">
          <Card className="sticky top-24 shadow-soft">
            <CardHeader className="space-y-2">
              <CardTitle className="text-base">Итоги</CardTitle>
              <p className="text-sm text-muted-foreground">Сводка по текущему заказу.</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3">
                <div className="rounded-2xl bg-muted/50 p-4">
                  <p className="text-xs text-muted-foreground">Товаров</p>
                  <p className="mt-1 text-2xl font-semibold tracking-tight">{formatCount(totalItems)}</p>
                </div>
                <div className="rounded-2xl bg-muted/50 p-4">
                  <p className="text-xs text-muted-foreground">Количество</p>
                  <p className="mt-1 text-2xl font-semibold tracking-tight">{formatCount(totalQuantity)}</p>
                </div>
                <div className="rounded-2xl bg-muted/50 p-4">
                  <p className="text-xs text-muted-foreground">Итого</p>
                  <p className="mt-1 text-2xl font-semibold tracking-tight">{formatMoney(subtotal.toFixed(2))}</p>
                </div>
              </div>

              <Button
                type="button"
                className="w-full"
                disabled={!canSubmit}
                onClick={() =>
                  mutation.mutate({
                    customer_name: customerName.trim() || null,
                    customer_phone: customerPhone.trim() || null,
                    customer_address: customerAddress.trim() || null,
                    notes: orderTitle.trim() || null,
                    items: items.map((item) => ({
                      product_id: item.product.id,
                      quantity: item.quantity,
                      discount_amount: 0,
                    })),
                  })
                }
              >
                {mutation.isPending ? "Создаём заказ…" : "Создать заказ"}
              </Button>

              {mutation.isError ? (
                <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {extractErrorMessage(mutation.error)}
                </p>
              ) : null}
            </CardContent>
          </Card>
        </aside>
      </div>

      <div className="fixed inset-x-4 bottom-20 z-30 lg:hidden">
        <Card className="shadow-soft">
          <CardContent className="space-y-3 p-4">
            <div className="grid grid-cols-3 gap-2 text-center text-sm">
              <div className="rounded-2xl bg-muted/50 p-3">
                <p className="text-[11px] text-muted-foreground">Товаров</p>
                <p className="mt-1 font-semibold">{formatCount(totalItems)}</p>
              </div>
              <div className="rounded-2xl bg-muted/50 p-3">
                <p className="text-[11px] text-muted-foreground">Количество</p>
                <p className="mt-1 font-semibold">{formatCount(totalQuantity)}</p>
              </div>
              <div className="rounded-2xl bg-muted/50 p-3">
                <p className="text-[11px] text-muted-foreground">Итого</p>
                <p className="mt-1 font-semibold">{formatMoney(subtotal.toFixed(2))}</p>
              </div>
            </div>

            <Button
              type="button"
              className="w-full"
              disabled={!canSubmit}
              onClick={() =>
                mutation.mutate({
                  customer_name: customerName.trim() || null,
                  customer_phone: customerPhone.trim() || null,
                  customer_address: customerAddress.trim() || null,
                  notes: orderTitle.trim() || null,
                  items: items.map((item) => ({
                    product_id: item.product.id,
                    quantity: item.quantity,
                    discount_amount: 0,
                  })),
                })
              }
            >
              {mutation.isPending ? "Создаём заказ…" : "Создать заказ"}
            </Button>
          </CardContent>
        </Card>
      </div>

      {mutation.isError ? (
        <div className="lg:hidden">
          <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {extractErrorMessage(mutation.error)}
          </p>
        </div>
      ) : null}
    </div>
  );
}
