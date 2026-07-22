"use client";

import { useEffect, useMemo, useState, type ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getMyCompany, updateMyCompany } from "@/lib/company";
import { extractErrorMessage } from "@/lib/errors";

type FormState = {
  currency: string;
  tax_percentage: string;
  footer_text: string;
  payment_information: string;
  notes: string;
};

const emptyState: FormState = {
  currency: "KZT",
  tax_percentage: "0",
  footer_text: "",
  payment_information: "",
  notes: "",
};

export default function InvoiceSettingsPage(): ReactElement {
  const queryClient = useQueryClient();
  const companyQuery = useQuery({
    queryKey: ["company-profile"],
    queryFn: getMyCompany,
  });
  const company = companyQuery.data;
  const [message, setMessage] = useState<string | null>(null);

  const initialState = useMemo<FormState>(() => {
    if (!company) {
      return emptyState;
    }
    return {
      currency: company.currency ?? "KZT",
      tax_percentage: company.tax_percentage ?? "0",
      footer_text: company.footer_text ?? "",
      payment_information: company.payment_information ?? "",
      notes: company.notes ?? "",
    };
  }, [company]);

  const [formState, setFormState] = useState<FormState>(emptyState);

  useEffect(() => {
    setFormState(initialState);
  }, [initialState]);

  const mutation = useMutation({
    mutationFn: updateMyCompany,
    onSuccess: async () => {
      setMessage("Настройки счёта успешно сохранены.");
      await queryClient.invalidateQueries({ queryKey: ["company-profile"] });
    },
  });

  const submit = (): void => {
    setMessage(null);
    mutation.mutate({
      currency: formState.currency.trim().toUpperCase(),
      tax_percentage: formState.tax_percentage.trim(),
      footer_text: formState.footer_text.trim() || null,
      payment_information: formState.payment_information.trim() || null,
      notes: formState.notes.trim() || null,
    });
  };

  return (
    <Card>
      <CardHeader>
        <Badge className="w-fit">Настройки счёта</Badge>
        <CardTitle>Налоги, платёжная информация и подвал</CardTitle>
        <CardDescription>Эти значения подставляются в каждый PDF-счёт, который создаёт backend.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-5 lg:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="defaultCurrency">Валюта по умолчанию</Label>
          <Input
            id="defaultCurrency"
            value={formState.currency}
            onChange={(event) => setFormState((current) => ({ ...current, currency: event.target.value }))}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="taxPercentage">Процент налога</Label>
          <Input
            id="taxPercentage"
            value={formState.tax_percentage}
            onChange={(event) => setFormState((current) => ({ ...current, tax_percentage: event.target.value }))}
          />
        </div>
        <div className="lg:col-span-2 space-y-2">
          <Label htmlFor="paymentInformation">Платёжная информация</Label>
          <textarea
            id="paymentInformation"
            value={formState.payment_information}
            onChange={(event) =>
              setFormState((current) => ({ ...current, payment_information: event.target.value }))
            }
            className="min-h-28 w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        <div className="lg:col-span-2 space-y-2">
          <Label htmlFor="footerText">Текст подвала</Label>
          <textarea
            id="footerText"
            value={formState.footer_text}
            onChange={(event) => setFormState((current) => ({ ...current, footer_text: event.target.value }))}
            className="min-h-24 w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        <div className="lg:col-span-2 space-y-2">
          <Label htmlFor="invoiceNotes">Заметки</Label>
          <textarea
            id="invoiceNotes"
            value={formState.notes}
            onChange={(event) => setFormState((current) => ({ ...current, notes: event.target.value }))}
            className="min-h-24 w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        {message ? (
          <p className="lg:col-span-2 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-300">
            {message}
          </p>
        ) : null}
        {mutation.isError ? (
          <p className="lg:col-span-2 rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {extractErrorMessage(mutation.error)}
          </p>
        ) : null}
        <div className="lg:col-span-2 flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => setFormState(initialState)} disabled={mutation.isPending}>
            Сбросить
          </Button>
          <Button type="button" onClick={submit} disabled={mutation.isPending}>
            {mutation.isPending ? "Сохраняем..." : "Сохранить настройки счёта"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
