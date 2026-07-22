"use client";

import { useMemo, useState, type ReactElement } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createOrder } from "@/lib/orders";
import { extractErrorMessage } from "@/lib/errors";

type DraftItem = {
  product_id: string;
  quantity: string;
  discount_amount: string;
};

const emptyItem = (): DraftItem => ({ product_id: "", quantity: "1", discount_amount: "0" });

export default function NewOrderPage(): ReactElement {
  const router = useRouter();
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [customerAddress, setCustomerAddress] = useState("");
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<"draft" | "confirmed" | "completed" | "cancelled">("draft");
  const [items, setItems] = useState<DraftItem[]>([emptyItem()]);

  const mutation = useMutation({
    mutationFn: createOrder,
    onSuccess: (order) => {
      router.push(`/orders/${order.id}`);
    },
  });

  const canSubmit = useMemo(
    () => items.length > 0 && items.every((item) => item.product_id.trim().length > 0 && Number(item.quantity) > 0),
    [items],
  );

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <Badge>Создание заказа</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Ручной ввод заказа</h1>
        <p className="max-w-2xl text-muted-foreground">
          Ищите товары, добавляйте количество, проверяйте итоги и сохраняйте заказ, не покидая панель.
        </p>
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <CardHeader>
          <CardTitle>Данные клиента</CardTitle>
          <CardDescription>Быстрый ввод, а все суммы рассчитывает backend.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="customerName">Имя клиента</Label>
              <Input id="customerName" value={customerName} onChange={(event) => setCustomerName(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="customerPhone">Телефон</Label>
              <Input id="customerPhone" value={customerPhone} onChange={(event) => setCustomerPhone(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="customerAddress">Адрес</Label>
              <Input
                id="customerAddress"
                value={customerAddress}
                onChange={(event) => setCustomerAddress(event.target.value)}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="notes">Комментарий</Label>
              <textarea
                id="notes"
                rows={4}
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                className="w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Например: доставка в пятницу после обеда."
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="status">Статус</Label>
              <select
                id="status"
                className="flex h-11 w-full rounded-2xl border border-input bg-background px-4 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
                value={status}
                onChange={(event) => setStatus(event.target.value as typeof status)}
              >
                <option value="draft">Черновик</option>
                <option value="confirmed">Подтверждён</option>
                <option value="completed">Выполнен</option>
                <option value="cancelled">Отменён</option>
              </select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
          <CardTitle>Позиции</CardTitle>
          <CardDescription>В режиме проверки будут видны цена, скидка, налог и итоги по каждой строке.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {items.map((item, index) => (
              <div key={index} className="grid gap-3 rounded-2xl border p-4">
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="space-y-2 md:col-span-3">
                    <Label>ID товара</Label>
                    <Input
                      value={item.product_id}
                      onChange={(event) =>
                        setItems((current) =>
                          current.map((currentItem, currentIndex) =>
                            currentIndex === index ? { ...currentItem, product_id: event.target.value } : currentItem,
                          ),
                        )
                      }
                      placeholder="Вставьте ID товара"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Количество</Label>
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
                    <Label>Скидка</Label>
                    <Input
                      value={item.discount_amount}
                      onChange={(event) =>
                        setItems((current) =>
                          current.map((currentItem, currentIndex) =>
                            currentIndex === index
                              ? { ...currentItem, discount_amount: event.target.value }
                              : currentItem,
                          ),
                        )
                      }
                    />
                  </div>
                </div>
                <div className="flex justify-end">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setItems((current) => current.filter((_, currentIndex) => currentIndex !== index))}
                    disabled={items.length === 1}
                  >
                    Удалить строку
                  </Button>
                </div>
              </div>
            ))}
            <div className="flex flex-wrap gap-3">
              <Button type="button" variant="outline" onClick={() => setItems((current) => [...current, emptyItem()])}>
                Добавить строку
              </Button>
              <Button
                type="button"
                className="w-full"
                disabled={mutation.isPending || !canSubmit}
                onClick={() =>
                  mutation.mutate({
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
                  })
                }
              >
                {mutation.isPending ? "Сохраняем..." : "Сохранить черновик"}
              </Button>
            </div>
            {mutation.isError ? (
              <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {extractErrorMessage(mutation.error)}
              </p>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
