"use client";

import { useEffect, useMemo, useRef, useState, type ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getMyCompany, updateMyCompany, uploadCompanyLogo, uploadInvoiceLogo } from "@/lib/company";
import { extractErrorMessage } from "@/lib/errors";

type FormState = {
  invoice_prefix: string;
  invoice_number_format: string;
};

const emptyState: FormState = {
  invoice_prefix: "INV",
  invoice_number_format: "{prefix}-{number:06d}",
};

export default function BrandingPage(): ReactElement {
  const queryClient = useQueryClient();
  const companyQuery = useQuery({
    queryKey: ["company-profile"],
    queryFn: getMyCompany,
  });
  const company = companyQuery.data;
  const [formState, setFormState] = useState<FormState>(emptyState);
  const [message, setMessage] = useState<string | null>(null);
  const companyLogoRef = useRef<HTMLInputElement | null>(null);
  const invoiceLogoRef = useRef<HTMLInputElement | null>(null);
  const [companyLogoFile, setCompanyLogoFile] = useState<File | null>(null);
  const [invoiceLogoFile, setInvoiceLogoFile] = useState<File | null>(null);

  const initialState = useMemo<FormState>(() => {
    if (!company) {
      return emptyState;
    }
    return {
      invoice_prefix: company.invoice_prefix ?? "INV",
      invoice_number_format: company.invoice_number_format ?? "{prefix}-{number:06d}",
    };
  }, [company]);

  useEffect(() => {
    setFormState(initialState);
  }, [initialState]);

  const mutation = useMutation({
    mutationFn: async () => {
      if (companyLogoFile) {
        await uploadCompanyLogo(companyLogoFile);
      }
      if (invoiceLogoFile) {
        await uploadInvoiceLogo(invoiceLogoFile);
      }
      return updateMyCompany({
        invoice_prefix: formState.invoice_prefix.trim(),
        invoice_number_format: formState.invoice_number_format.trim(),
      });
    },
    onSuccess: async () => {
      setMessage("Брендинг успешно обновлён.");
      setCompanyLogoFile(null);
      setInvoiceLogoFile(null);
      if (companyLogoRef.current) {
        companyLogoRef.current.value = "";
      }
      if (invoiceLogoRef.current) {
        invoiceLogoRef.current.value = "";
      }
      await queryClient.invalidateQueries({ queryKey: ["company-profile"] });
    },
  });

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_0.85fr]">
      <Card>
        <CardHeader>
          <Badge className="w-fit">Брендинг</Badge>
          <CardTitle>Логотип компании и оформление счетов</CardTitle>
          <CardDescription>Сохраняйте единый визуальный стиль в заказах, счетах и PDF.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="companyLogo">Логотип компании</Label>
            <Input
              ref={companyLogoRef}
              id="companyLogo"
              type="file"
              accept="image/png,image/jpeg,image/webp,image/svg+xml"
              onChange={(event) => setCompanyLogoFile(event.target.files?.[0] ?? null)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="invoiceLogo">Логотип счёта</Label>
            <Input
              ref={invoiceLogoRef}
              id="invoiceLogo"
              type="file"
              accept="image/png,image/jpeg,image/webp,image/svg+xml"
              onChange={(event) => setInvoiceLogoFile(event.target.files?.[0] ?? null)}
            />
          </div>
          <div className="grid gap-5 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="invoicePrefix">Префикс счёта</Label>
              <Input
                id="invoicePrefix"
                value={formState.invoice_prefix}
                onChange={(event) => setFormState((current) => ({ ...current, invoice_prefix: event.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="invoiceFormat">Формат номера счёта</Label>
              <Input
                id="invoiceFormat"
                value={formState.invoice_number_format}
                onChange={(event) =>
                  setFormState((current) => ({ ...current, invoice_number_format: event.target.value }))
                }
              />
            </div>
          </div>
          {message ? (
            <p className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-300">
              {message}
            </p>
          ) : null}
          {mutation.isError ? (
            <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {extractErrorMessage(mutation.error)}
            </p>
          ) : null}
          <div className="flex justify-end">
            <Button type="button" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
              {mutation.isPending ? "Сохраняем..." : "Сохранить"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Предпросмотр</CardTitle>
          <CardDescription>Минималистичное оформление счёта с мягкими отступами и округлёнными формами.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-3xl border bg-muted/30 p-6">
            <div className="flex items-center justify-between gap-4">
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Логотип компании</p>
                <p className="font-medium">{company?.name ?? "Ваша компания"}</p>
              </div>
              <Badge variant="outline">{company?.invoice_prefix ?? formState.invoice_prefix}</Badge>
            </div>
            <div className="mt-6 space-y-3">
              <div className="h-3 w-2/3 rounded-full bg-foreground/10" />
              <div className="h-3 w-1/2 rounded-full bg-foreground/10" />
              <div className="h-3 w-3/4 rounded-full bg-foreground/10" />
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            {company?.logo_url ? "Логотип компании загружен." : "Загрузите логотип, чтобы брендировать пространство."}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
