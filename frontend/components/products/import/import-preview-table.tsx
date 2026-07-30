"use client";

import { Plus, Trash2 } from "lucide-react";
import type { ReactElement } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { ProductImportRow } from "@/types/product-import";

type ImportPreviewTableProps = {
  rows: ProductImportRow[];
  onChange: (rows: ProductImportRow[]) => void;
};

function createEmptyRow(): ProductImportRow {
  return {
    name: "",
    price: "",
    category: "",
    manufacturer: "",
    size: "",
  };
}

export function ImportPreviewTable({ rows, onChange }: ImportPreviewTableProps): ReactElement {
  const updateRow = (index: number, field: keyof ProductImportRow, value: string) => {
    const nextRows = rows.map((row, rowIndex) =>
      rowIndex === index ? { ...row, [field]: value || null } : row,
    );
    onChange(nextRows);
  };

  const removeRow = (index: number) => {
    onChange(rows.filter((_, rowIndex) => rowIndex !== index));
  };

  const addRow = () => {
    onChange([...rows, createEmptyRow()]);
  };

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-2xl border border-border/70 bg-background">
        <div className="hidden overflow-x-auto md:block">
          <table className="min-w-full text-sm">
            <thead className="border-b border-border/70 bg-muted/30">
              <tr className="text-left text-muted-foreground">
                <th className="px-4 py-3 font-medium">Название</th>
                <th className="px-4 py-3 font-medium">Цена</th>
                <th className="px-4 py-3 font-medium">Категория</th>
                <th className="px-4 py-3 font-medium">Производитель</th>
                <th className="px-4 py-3 font-medium">Размер</th>
                <th className="px-4 py-3 font-medium" />
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={`import-row-${index}`} className="border-b border-border/50 last:border-b-0">
                  <td className="px-4 py-2">
                    <Input
                      value={row.name}
                      onChange={(event) => updateRow(index, "name", event.target.value)}
                      placeholder="Название"
                      className="min-w-[180px] rounded-xl border-border/70"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <Input
                      value={String(row.price ?? "")}
                      onChange={(event) => updateRow(index, "price", event.target.value)}
                      placeholder="0"
                      inputMode="decimal"
                      className="min-w-[120px] rounded-xl border-border/70"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <Input
                      value={row.category ?? ""}
                      onChange={(event) => updateRow(index, "category", event.target.value)}
                      placeholder="Категория"
                      className="min-w-[140px] rounded-xl border-border/70"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <Input
                      value={row.manufacturer ?? ""}
                      onChange={(event) => updateRow(index, "manufacturer", event.target.value)}
                      placeholder="Производитель"
                      className="min-w-[140px] rounded-xl border-border/70"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <Input
                      value={row.size ?? ""}
                      onChange={(event) => updateRow(index, "size", event.target.value)}
                      placeholder="Размер"
                      className="min-w-[100px] rounded-xl border-border/70"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeRow(index)}
                      aria-label="Удалить строку"
                      className="h-9 w-9 rounded-xl p-0 text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="space-y-3 p-4 md:hidden">
          {rows.map((row, index) => (
            <div key={`import-row-mobile-${index}`} className="space-y-3 rounded-2xl border border-border/70 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-muted-foreground">Строка {index + 1}</span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeRow(index)}
                  aria-label="Удалить строку"
                  className="h-9 w-9 rounded-xl p-0 text-muted-foreground hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
              <Input
                value={row.name}
                onChange={(event) => updateRow(index, "name", event.target.value)}
                placeholder="Название"
                className="rounded-xl border-border/70"
              />
              <Input
                value={String(row.price ?? "")}
                onChange={(event) => updateRow(index, "price", event.target.value)}
                placeholder="Цена"
                inputMode="decimal"
                className="rounded-xl border-border/70"
              />
              <Input
                value={row.category ?? ""}
                onChange={(event) => updateRow(index, "category", event.target.value)}
                placeholder="Категория"
                className="rounded-xl border-border/70"
              />
              <Input
                value={row.manufacturer ?? ""}
                onChange={(event) => updateRow(index, "manufacturer", event.target.value)}
                placeholder="Производитель"
                className="rounded-xl border-border/70"
              />
              <Input
                value={row.size ?? ""}
                onChange={(event) => updateRow(index, "size", event.target.value)}
                placeholder="Размер"
                className="rounded-xl border-border/70"
              />
            </div>
          ))}
        </div>
      </div>

      <Button type="button" variant="outline" onClick={addRow} className="rounded-2xl">
        <Plus className="mr-2 h-4 w-4" />
        Добавить строку
      </Button>
    </div>
  );
}
