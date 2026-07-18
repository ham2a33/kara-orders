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
  name: string;
  email: string;
  bin_tax_id: string;
  phone: string;
  website: string;
  timezone: string;
  language: string;
  currency: string;
  address: string;
  notes: string;
};

const emptyState: FormState = {
  name: "",
  email: "",
  bin_tax_id: "",
  phone: "",
  website: "",
  timezone: "Asia/Almaty",
  language: "en",
  currency: "KZT",
  address: "",
  notes: "",
};

const fields: Array<{ id: keyof FormState; label: string; type?: string }> = [
  { id: "name", label: "Company name" },
  { id: "email", label: "Company email", type: "email" },
  { id: "bin_tax_id", label: "BIN / Tax ID" },
  { id: "phone", label: "Phone" },
  { id: "website", label: "Website" },
  { id: "timezone", label: "Timezone" },
  { id: "language", label: "Language" },
  { id: "currency", label: "Currency" },
  { id: "address", label: "Address" },
];

export default function CompanySettingsPage(): ReactElement {
  const queryClient = useQueryClient();
  const companyQuery = useQuery({
    queryKey: ["company-profile"],
    queryFn: getMyCompany,
  });
  const company = companyQuery.data;

  const initialState = useMemo<FormState>(() => {
    if (!company) {
      return emptyState;
    }
    return {
      name: company.name ?? "",
      email: company.email ?? "",
      bin_tax_id: company.bin_tax_id ?? "",
      phone: company.phone ?? "",
      website: company.website ?? "",
      timezone: company.timezone ?? "Asia/Almaty",
      language: company.language ?? "en",
      currency: company.currency ?? "KZT",
      address: company.address ?? "",
      notes: company.notes ?? "",
    };
  }, [company]);

  const [formState, setFormState] = useState<FormState>(emptyState);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    setFormState(initialState);
  }, [initialState]);

  const mutation = useMutation({
    mutationFn: updateMyCompany,
    onSuccess: async () => {
      setMessage("Company settings saved successfully.");
      await queryClient.invalidateQueries({ queryKey: ["company-profile"] });
    },
  });

  const submit = (): void => {
    setMessage(null);
    mutation.mutate({
      name: formState.name.trim(),
      email: formState.email.trim() || null,
      bin_tax_id: formState.bin_tax_id.trim() || null,
      phone: formState.phone.trim() || null,
      website: formState.website.trim() || null,
      timezone: formState.timezone.trim() || null,
      language: formState.language.trim() || null,
      currency: formState.currency.trim().toUpperCase() || null,
      address: formState.address.trim() || null,
      notes: formState.notes.trim() || null,
    });
  };

  return (
    <Card>
      <CardHeader>
        <Badge className="w-fit">Company Settings</Badge>
        <CardTitle>Business information and contact details</CardTitle>
        <CardDescription>Update the core company record that every invoice and order references.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-5 lg:grid-cols-2">
        {fields.map((field) => (
          <div key={field.id} className="space-y-2">
            <Label htmlFor={field.id}>{field.label}</Label>
            <Input
              id={field.id}
              type={field.type ?? "text"}
              value={formState[field.id]}
              onChange={(event) =>
                setFormState((current) => ({
                  ...current,
                  [field.id]: event.target.value,
                }))
              }
            />
          </div>
        ))}
        <div className="lg:col-span-2 space-y-2">
          <Label htmlFor="notes">Company notes</Label>
          <textarea
            id="notes"
            value={formState.notes}
            onChange={(event) => setFormState((current) => ({ ...current, notes: event.target.value }))}
            className="min-h-32 w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
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
        <div className="lg:col-span-2 flex flex-wrap justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => setFormState(initialState)} disabled={mutation.isPending}>
            Reset
          </Button>
          <Button type="button" onClick={submit} disabled={mutation.isPending}>
            {mutation.isPending ? "Saving..." : "Save company settings"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
