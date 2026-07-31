"use client";

import { useEffect, useMemo, useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Copy, FileDown, Loader2, MessageCircle, Printer, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { formatDate, formatMoney } from "@/components/platform/shared";
import { extractErrorMessage } from "@/lib/errors";
import {
  copyReceiptLink,
  downloadOrderReceiptPdf,
  normalizeWhatsAppPhone,
  printOrderReceipt,
  shareViaWhatsApp,
} from "@/lib/order-share";
import { getInvoicePreview } from "@/lib/orders";
import type { InvoiceCompanyPreview, Order } from "@/types/orders";

type OrderCreatedDialogProps = {
  order: Order;
  open: boolean;
  onClose: () => void;
};

function ActionButton({
  icon,
  label,
  onClick,
  disabled,
  hint,
}: {
  icon: ReactElement;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  hint?: string;
}): ReactElement {
  return (
    <div className="space-y-1">
      <Button
        type="button"
        variant="outline"
        className="h-14 w-full justify-start gap-3 rounded-2xl text-base"
        onClick={onClick}
        disabled={disabled}
      >
        {icon}
        {label}
      </Button>
      {hint ? <p className="px-1 text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

export function OrderCreatedDialog({ order, open, onClose }: OrderCreatedDialogProps): ReactElement | null {
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const previewQuery = useQuery({
    queryKey: ["order-invoice", order.id, "created-dialog"],
    queryFn: () => getInvoicePreview(order.id),
    enabled: open,
  });

  const company: InvoiceCompanyPreview | undefined = previewQuery.data?.company;
  const currency = company?.currency ?? "KZT";
  const whatsAppPhone = useMemo(() => normalizeWhatsAppPhone(order.customer_phone), [order.customer_phone]);
  const canWhatsApp = Boolean(whatsAppPhone);

  useEffect(() => {
    if (!open) {
      setBusyAction(null);
      setFeedback(null);
      setError(null);
    }
  }, [open]);

  useEffect(() => {
    if (!open) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  const runAction = async (actionId: string, task: () => Promise<void>): Promise<void> => {
    setBusyAction(actionId);
    setError(null);
    setFeedback(null);
    try {
      await task();
    } catch (caught) {
      setError(extractErrorMessage(caught));
    } finally {
      setBusyAction(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="order-created-title"
        className="max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-3xl border bg-background shadow-2xl"
      >
        <div className="flex items-start justify-between gap-3 border-b px-6 py-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-5 w-5" />
              <h2 id="order-created-title" className="text-lg font-semibold">
                Заказ успешно создан
              </h2>
            </div>
            <p className="text-sm text-muted-foreground">Отправьте чек клиенту или сохраните PDF.</p>
          </div>
          <Button type="button" variant="ghost" size="sm" className="h-9 w-9 p-0" onClick={onClose} aria-label="Закрыть">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-5 px-6 py-5">
          <dl className="grid gap-3 rounded-2xl bg-muted/40 p-4 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Номер заказа</dt>
              <dd className="font-medium">№{order.invoice_number}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Покупатель</dt>
              <dd className="text-right font-medium">{order.customer_name?.trim() || "—"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Телефон</dt>
              <dd className="font-medium">{order.customer_phone?.trim() || "—"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Дата</dt>
              <dd className="font-medium">{formatDate(order.created_at)}</dd>
            </div>
            <div className="flex justify-between gap-4 border-t pt-3">
              <dt className="font-medium">Итого</dt>
              <dd className="text-lg font-bold tabular-nums">{formatMoney(order.total, currency)}</dd>
            </div>
          </dl>

          <div className="grid gap-3">
            <ActionButton
              icon={busyAction === "pdf" ? <Loader2 className="h-5 w-5 animate-spin" /> : <FileDown className="h-5 w-5" />}
              label="Скачать PDF"
              disabled={busyAction !== null}
              onClick={() =>
                runAction("pdf", async () => {
                  await downloadOrderReceiptPdf(order.id, order.invoice_number);
                  setFeedback("PDF сохранён на устройство.");
                })
              }
            />
            <ActionButton
              icon={<Printer className="h-5 w-5" />}
              label="Распечатать"
              disabled={busyAction !== null}
              onClick={() => {
                printOrderReceipt(order.id);
                setFeedback("Открыта страница печати чека.");
              }}
            />
            <ActionButton
              icon={
                busyAction === "whatsapp" ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <MessageCircle className="h-5 w-5" />
                )
              }
              label="Отправить в WhatsApp"
              disabled={!canWhatsApp || !company || busyAction !== null}
              hint={!canWhatsApp ? "У покупателя не указан номер телефона." : undefined}
              onClick={() =>
                runAction("whatsapp", async () => {
                  if (!company) {
                    throw new Error("Не удалось загрузить данные магазина.");
                  }
                  await shareViaWhatsApp({ order, company, customerPhone: order.customer_phone });
                  setFeedback("PDF скачан. WhatsApp открыт с готовым текстом — прикрепите файл.");
                })
              }
            />
            <ActionButton
              icon={busyAction === "copy" ? <Loader2 className="h-5 w-5 animate-spin" /> : <Copy className="h-5 w-5" />}
              label="Копировать ссылку"
              disabled={busyAction !== null}
              onClick={() =>
                runAction("copy", async () => {
                  const link = await copyReceiptLink(order.id);
                  setFeedback(`Ссылка скопирована: ${link}`);
                })
              }
            />
          </div>

          {previewQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Загружаем данные чека…</p>
          ) : null}
          {feedback ? (
            <p className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-800 dark:text-emerald-200">
              {feedback}
            </p>
          ) : null}
          {error ? (
            <p className="rounded-xl border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          ) : null}

          <Button type="button" variant="secondary" className="h-12 w-full rounded-2xl" onClick={onClose}>
            Закрыть
          </Button>
        </div>
      </div>
    </div>
  );
}
