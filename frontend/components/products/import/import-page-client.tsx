"use client";

import Link from "next/link";
import { useCallback, useMemo, useRef, useState, type ChangeEvent, type DragEvent, type ReactElement } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, FileSpreadsheet, FileText, ImageIcon, Loader2, Upload } from "lucide-react";

import { ImportPreviewTable } from "@/components/products/import/import-preview-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { confirmProductImport, parseImportFile } from "@/lib/product-import";
import { extractErrorMessage } from "@/lib/errors";
import {
  IMPORT_ACCEPT,
  IMPORT_FIELD_LABELS,
  IMPORT_SOURCE_LABELS,
  type ImportSource,
  type ProductImportParseResponse,
  type ProductImportRow,
} from "@/types/product-import";

type Step = "upload" | "preview" | "done";

const SOURCE_OPTIONS: Array<{
  id: ImportSource;
  icon: typeof FileSpreadsheet;
  title: string;
  description: string;
}> = [
  {
    id: "excel",
    icon: FileSpreadsheet,
    title: "Excel / CSV",
    description: "Загрузите .xlsx или .csv с прайсом или каталогом",
  },
  {
    id: "pdf",
    icon: FileText,
    title: "PDF",
    description: "ИИ извлечёт товары из прайс-листа",
  },
  {
    id: "photo",
    icon: ImageIcon,
    title: "Фото",
    description: "Распознавание прайса, каталога или накладной",
  },
];

function isValidRow(row: ProductImportRow): boolean {
  const name = row.name.trim();
  const price = Number(String(row.price).replace(/\s/g, "").replace(",", "."));
  return name.length >= 2 && Number.isFinite(price) && price >= 0;
}

export function ImportPageClient(): ReactElement {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [source, setSource] = useState<ImportSource>("excel");
  const [step, setStep] = useState<Step>("upload");
  const [rows, setRows] = useState<ProductImportRow[]>([]);
  const [parseMeta, setParseMeta] = useState<Pick<ProductImportParseResponse, "columns" | "mapping"> | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [confirmResult, setConfirmResult] = useState<{ created: number; errors: number } | null>(null);

  const parseMutation = useMutation({
    mutationFn: (file: File) => parseImportFile(source, file),
    onSuccess: (data) => {
      setRows(data.rows);
      setParseMeta({ columns: data.columns, mapping: data.mapping });
      setStep("preview");
      setUploadError(null);
    },
    onError: (error) => {
      setUploadError(extractErrorMessage(error));
    },
  });

  const confirmMutation = useMutation({
    mutationFn: () =>
      confirmProductImport(
        rows
          .filter(isValidRow)
          .map((row) => ({
            ...row,
            name: row.name.trim(),
            price: Number(String(row.price).replace(/\s/g, "").replace(",", ".")),
            category: row.category?.trim() || null,
            manufacturer: row.manufacturer?.trim() || null,
            size: row.size?.trim() || null,
          })),
      ),
    onSuccess: (data) => {
      setConfirmResult({ created: data.created, errors: data.errors.length });
      setStep("done");
      void queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });

  const validRowCount = useMemo(() => rows.filter(isValidRow).length, [rows]);

  const mappingEntries = useMemo(() => {
    if (!parseMeta?.mapping) {
      return [];
    }
    return Object.entries(parseMeta.mapping).filter(([, field]) => field);
  }, [parseMeta]);

  const handleFile = useCallback(
    (file: File | null) => {
      if (!file) {
        return;
      }
      setUploadError(null);
      parseMutation.mutate(file);
    },
    [parseMutation],
  );

  const onFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFile(event.target.files?.[0] ?? null);
    event.target.value = "";
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragActive(false);
    handleFile(event.dataTransfer.files?.[0] ?? null);
  };

  const resetFlow = () => {
    setStep("upload");
    setRows([]);
    setParseMeta(null);
    setUploadError(null);
    setConfirmResult(null);
  };

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <Badge>Импорт</Badge>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">Импорт товаров</h1>
            <p className="max-w-2xl text-muted-foreground">
              Загрузите Excel, PDF или фото — проверьте данные в предпросмотре и добавьте товары в каталог одним
              подтверждением.
            </p>
          </div>
        </div>
        <Button asChild variant="outline" className="rounded-2xl">
          <Link href="/products">
            <ArrowLeft className="mr-2 h-4 w-4" />
            К каталогу
          </Link>
        </Button>
      </section>

      {step === "upload" && (
        <>
          <section className="grid gap-4 md:grid-cols-3">
            {SOURCE_OPTIONS.map((option) => {
              const Icon = option.icon;
              const active = source === option.id;
              return (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => setSource(option.id)}
                  className={`rounded-2xl border p-5 text-left transition-colors ${
                    active
                      ? "border-foreground/20 bg-muted/40 shadow-sm"
                      : "border-border/70 bg-background hover:border-foreground/10 hover:bg-muted/20"
                  }`}
                >
                  <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-background">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h2 className="font-medium">{option.title}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">{option.description}</p>
                </button>
              );
            })}
          </section>

          <Card className="rounded-3xl border-border/70 shadow-sm">
            <CardHeader>
              <CardTitle>Загрузка файла</CardTitle>
              <CardDescription>
                Формат: {IMPORT_SOURCE_LABELS[source]}. SKU создаётся автоматически при сохранении.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                role="button"
                tabIndex={0}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragActive(true);
                }}
                onDragLeave={() => setDragActive(false)}
                onDrop={onDrop}
                onClick={() => fileInputRef.current?.click()}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    fileInputRef.current?.click();
                  }
                }}
                className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed px-6 py-14 text-center transition-colors ${
                  dragActive ? "border-foreground/30 bg-muted/30" : "border-border/80 bg-muted/10 hover:bg-muted/20"
                }`}
              >
                {parseMutation.isPending ? (
                  <>
                    <Loader2 className="mb-4 h-8 w-8 animate-spin text-muted-foreground" />
                    <p className="font-medium">Обрабатываем файл…</p>
                  </>
                ) : (
                  <>
                    <Upload className="mb-4 h-8 w-8 text-muted-foreground" />
                    <p className="font-medium">Перетащите файл или нажмите для выбора</p>
                    <p className="mt-1 text-sm text-muted-foreground">{IMPORT_ACCEPT[source]}</p>
                  </>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept={IMPORT_ACCEPT[source]}
                className="hidden"
                onChange={onFileChange}
              />
              {uploadError ? <p className="mt-4 text-sm text-destructive">{uploadError}</p> : null}
            </CardContent>
          </Card>
        </>
      )}

      {step === "preview" && (
        <>
          {mappingEntries.length > 0 ? (
            <Card className="rounded-3xl border-border/70 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Сопоставление колонок</CardTitle>
                <CardDescription>Колонки из файла автоматически сопоставлены с полями каталога.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-3">
                  {mappingEntries.map(([column, field]) => (
                    <div
                      key={column}
                      className="flex items-center gap-2 rounded-2xl border border-border/70 bg-muted/20 px-3 py-2 text-sm"
                    >
                      <span className="font-medium">{column}</span>
                      <span className="text-muted-foreground">→</span>
                      <span>{field ? IMPORT_FIELD_LABELS[field] ?? field : column}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : null}

          <Card className="rounded-3xl border-border/70 shadow-sm">
            <CardHeader className="flex flex-row items-start justify-between gap-4">
              <div>
                <CardTitle>Предпросмотр</CardTitle>
                <CardDescription>
                  Проверьте и отредактируйте данные. Если указан размер, при сохранении название станет «Название —
                  Размер».
                </CardDescription>
              </div>
              <Badge>{validRowCount} готово</Badge>
            </CardHeader>
            <CardContent className="space-y-6">
              <ImportPreviewTable rows={rows} onChange={setRows} />

              {confirmMutation.error ? (
                <p className="text-sm text-destructive">{extractErrorMessage(confirmMutation.error)}</p>
              ) : null}

              <div className="flex flex-wrap gap-3">
                <Button type="button" variant="outline" onClick={resetFlow} className="rounded-2xl">
                  Загрузить другой файл
                </Button>
                <Button
                  type="button"
                  onClick={() => confirmMutation.mutate()}
                  disabled={validRowCount === 0 || confirmMutation.isPending}
                  className="rounded-2xl"
                >
                  {confirmMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Импорт…
                    </>
                  ) : (
                    <>Импортировать {validRowCount} товаров</>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {step === "done" && confirmResult ? (
        <Card className="rounded-3xl border-border/70 shadow-sm">
          <CardContent className="flex flex-col items-center gap-4 py-16 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/10">
              <CheckCircle2 className="h-7 w-7 text-emerald-600" />
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-semibold">Импорт завершён</h2>
              <p className="text-muted-foreground">
                Добавлено товаров: {confirmResult.created}
                {confirmResult.errors > 0 ? ` · Ошибок: ${confirmResult.errors}` : ""}
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-3 pt-2">
              <Button asChild className="rounded-2xl">
                <Link href="/products">Перейти в каталог</Link>
              </Button>
              <Button type="button" variant="outline" onClick={resetFlow} className="rounded-2xl">
                Импортировать ещё
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
