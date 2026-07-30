"use client";

import { useState, type ReactElement, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type ModalShellProps = {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
};

export function ModalShell({ open, title, onClose, children }: ModalShellProps): ReactElement | null {
  if (!open) {
    return null;
  }
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-3xl border bg-background p-6 shadow-lg"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="catalog-modal-title"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 id="catalog-modal-title" className="text-lg font-semibold">
            {title}
          </h2>
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>
            Закрыть
          </Button>
        </div>
        {children}
      </div>
    </div>
  );
}

type BulkPriceModalProps = {
  open: boolean;
  selectedCount: number;
  pending: boolean;
  onClose: () => void;
  onConfirm: (payload: {
    field: "price" | "cost";
    operation: "increase" | "decrease";
    mode: "percentage" | "fixed";
    value: string;
  }) => void;
};

export function BulkPriceModal({ open, selectedCount, pending, onClose, onConfirm }: BulkPriceModalProps): ReactElement {
  const [field, setField] = useState<"price" | "cost">("price");
  const [operation, setOperation] = useState<"increase" | "decrease">("increase");
  const [mode, setMode] = useState<"percentage" | "fixed">("percentage");
  const [value, setValue] = useState("10");

  return (
    <ModalShell open={open} title="Изменить цены" onClose={onClose}>
      <div className="space-y-5 text-sm">
        <fieldset className="space-y-2">
          <legend className="font-medium">Поле</legend>
          <label className="flex items-center gap-2">
            <input type="radio" checked={field === "price"} onChange={() => setField("price")} />
            Цена продажи
          </label>
          <label className="flex items-center gap-2">
            <input type="radio" checked={field === "cost"} onChange={() => setField("cost")} />
            Себестоимость
          </label>
        </fieldset>

        <fieldset className="space-y-2">
          <legend className="font-medium">Операция</legend>
          <label className="flex items-center gap-2">
            <input type="radio" checked={operation === "increase"} onChange={() => setOperation("increase")} />
            Увеличить
          </label>
          <label className="flex items-center gap-2">
            <input type="radio" checked={operation === "decrease"} onChange={() => setOperation("decrease")} />
            Уменьшить
          </label>
        </fieldset>

        <fieldset className="space-y-2">
          <legend className="font-medium">Значение</legend>
          <label className="flex items-center gap-2">
            <input type="radio" checked={mode === "percentage"} onChange={() => setMode("percentage")} />
            Процент
          </label>
          <label className="flex items-center gap-2">
            <input type="radio" checked={mode === "fixed"} onChange={() => setMode("fixed")} />
            Фиксированная сумма (KZT)
          </label>
          <Input
            inputMode="decimal"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder={mode === "percentage" ? "10" : "500"}
          />
        </fieldset>

        <p className="rounded-2xl bg-muted/50 px-4 py-3 text-muted-foreground">
          Затронуто товаров: <span className="font-medium text-foreground">{selectedCount}</span>
        </p>

        <Button
          type="button"
          className="w-full"
          disabled={pending || !value.trim() || selectedCount === 0}
          onClick={() => onConfirm({ field, operation, mode, value: value.trim() })}
        >
          {pending ? "Применяем..." : "Подтвердить"}
        </Button>
      </div>
    </ModalShell>
  );
}

const VAT_PRESETS: Array<{ label: string; value: string | null }> = [
  { label: "0%", value: "0" },
  { label: "5%", value: "5" },
  { label: "10%", value: "10" },
  { label: "12%", value: "12" },
  { label: "20%", value: "20" },
  { label: "Без НДС", value: null },
];

type BulkVatModalProps = {
  open: boolean;
  selectedCount: number;
  pending: boolean;
  onClose: () => void;
  onConfirm: (taxRate: string | null) => void;
};

export function BulkVatModal({ open, selectedCount, pending, onClose, onConfirm }: BulkVatModalProps): ReactElement {
  const [selected, setSelected] = useState<string | null>("12");

  return (
    <ModalShell open={open} title="Изменить НДС" onClose={onClose}>
      <div className="space-y-5 text-sm">
        <div className="grid gap-2">
          {VAT_PRESETS.map((preset) => (
            <label key={preset.label} className="flex items-center gap-2 rounded-xl border px-3 py-2">
              <input
                type="radio"
                checked={selected === preset.value}
                onChange={() => setSelected(preset.value)}
              />
              {preset.label}
            </label>
          ))}
        </div>
        <p className="rounded-2xl bg-muted/50 px-4 py-3 text-muted-foreground">
          Затронуто товаров: <span className="font-medium text-foreground">{selectedCount}</span>
        </p>
        <Button
          type="button"
          className="w-full"
          disabled={pending || selectedCount === 0}
          onClick={() => onConfirm(selected)}
        >
          {pending ? "Применяем..." : "Подтвердить"}
        </Button>
      </div>
    </ModalShell>
  );
}

type BulkStatusModalProps = {
  open: boolean;
  selectedCount: number;
  pending: boolean;
  onClose: () => void;
  onConfirm: (isActive: boolean) => void;
};

export function BulkStatusModal({ open, selectedCount, pending, onClose, onConfirm }: BulkStatusModalProps): ReactElement {
  const [isActive, setIsActive] = useState(true);

  return (
    <ModalShell open={open} title="Изменить статус" onClose={onClose}>
      <div className="space-y-5 text-sm">
        <Label className="font-medium">Новый статус</Label>
        <label className="flex items-center gap-2">
          <input type="radio" checked={isActive} onChange={() => setIsActive(true)} />
          Активный
        </label>
        <label className="flex items-center gap-2">
          <input type="radio" checked={!isActive} onChange={() => setIsActive(false)} />
          Неактивный
        </label>
        <p className="rounded-2xl bg-muted/50 px-4 py-3 text-muted-foreground">
          Затронуто товаров: <span className="font-medium text-foreground">{selectedCount}</span>
        </p>
        <Button
          type="button"
          className="w-full"
          disabled={pending || selectedCount === 0}
          onClick={() => onConfirm(isActive)}
        >
          {pending ? "Применяем..." : "Подтвердить"}
        </Button>
      </div>
    </ModalShell>
  );
}

type BulkDeleteModalProps = {
  open: boolean;
  selectedCount: number;
  pending: boolean;
  onClose: () => void;
  onConfirm: () => void;
};

export function BulkDeleteModal({ open, selectedCount, pending, onClose, onConfirm }: BulkDeleteModalProps): ReactElement {
  return (
    <ModalShell open={open} title="Удалить товары" onClose={onClose}>
      <div className="space-y-5 text-sm">
        <p className="text-muted-foreground">
          Удалить выбранные товары ({selectedCount})? Действие можно отменить через восстановление.
        </p>
        <Button type="button" variant="secondary" className="w-full" disabled={pending || selectedCount === 0} onClick={onConfirm}>
          {pending ? "Удаляем..." : "Подтвердить удаление"}
        </Button>
      </div>
    </ModalShell>
  );
}

export function formatVatLabel(taxRate: string | null | undefined): string {
  if (taxRate === null || taxRate === undefined || taxRate === "") {
    return "Без НДС";
  }
  return `${taxRate}%`;
}
