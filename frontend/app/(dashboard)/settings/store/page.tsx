"use client";

import Image from "next/image";
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
  name: string;
  address: string;
  phone: string;
  email: string;
  website: string;
  instagram: string;
  bin_tax_id: string;
  director_name: string;
  welcome_message: string;
  receipt_signature: string;
  footer_text: string;
};

const emptyState: FormState = {
  name: "",
  address: "",
  phone: "",
  email: "",
  website: "",
  instagram: "",
  bin_tax_id: "",
  director_name: "",
  welcome_message: "",
  receipt_signature: "",
  footer_text: "",
};

export default function StoreInfoSettingsPage(): ReactElement {
  const queryClient = useQueryClient();
  const logoRef = useRef<HTMLInputElement | null>(null);
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);

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
      address: company.address ?? "",
      phone: company.phone ?? "",
      email: company.email ?? "",
      website: company.website ?? "",
      instagram: company.instagram ?? "",
      bin_tax_id: company.bin_tax_id ?? "",
      director_name: company.director_name ?? "",
      welcome_message: company.welcome_message ?? "",
      receipt_signature: company.receipt_signature ?? "",
      footer_text: company.footer_text ?? "",
    };
  }, [company]);

  const [formState, setFormState] = useState<FormState>(emptyState);

  useEffect(() => {
    setFormState(initialState);
  }, [initialState]);

  const mutation = useMutation({
    mutationFn: async () => {
      if (logoFile) {
        await uploadInvoiceLogo(logoFile);
        await uploadCompanyLogo(logoFile);
      }
      return updateMyCompany({
        name: formState.name.trim(),
        address: formState.address.trim() || null,
        phone: formState.phone.trim() || null,
        email: formState.email.trim() || null,
        website: formState.website.trim() || null,
        instagram: formState.instagram.trim() || null,
        bin_tax_id: formState.bin_tax_id.trim() || null,
        director_name: formState.director_name.trim() || null,
        welcome_message: formState.welcome_message.trim() || null,
        receipt_signature: formState.receipt_signature.trim() || null,
        footer_text: formState.footer_text.trim() || null,
      });
    },
    onSuccess: async () => {
      setMessage("Информация магазина сохранена.");
      setLogoFile(null);
      if (logoRef.current) {
        logoRef.current.value = "";
      }
      await queryClient.invalidateQueries({ queryKey: ["company-profile"] });
      await queryClient.invalidateQueries({ queryKey: ["company-me"] });
    },
  });

  const logoPreview = company?.invoice_logo_url ?? company?.logo_url;

  return (
    <Card>
      <CardHeader>
        <Badge className="w-fit">Настройки</Badge>
        <CardTitle>Информация магазина</CardTitle>
        <CardDescription>
          Эти данные отображаются на чеке и подставляются в сообщения WhatsApp. Без хардкода — только из профиля
          магазина.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-5 lg:grid-cols-2">
        <div className="space-y-2 lg:col-span-2">
          <Label htmlFor="store-name">Название магазина</Label>
          <Input
            id="store-name"
            value={formState.name}
            onChange={(event) => setFormState((current) => ({ ...current, name: event.target.value }))}
            placeholder="Строй Мир"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="store-address">Адрес</Label>
          <Input
            id="store-address"
            value={formState.address}
            onChange={(event) => setFormState((current) => ({ ...current, address: event.target.value }))}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="store-phone">Телефон</Label>
          <Input
            id="store-phone"
            value={formState.phone}
            onChange={(event) => setFormState((current) => ({ ...current, phone: event.target.value }))}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="store-email">Email</Label>
          <Input
            id="store-email"
            type="email"
            value={formState.email}
            onChange={(event) => setFormState((current) => ({ ...current, email: event.target.value }))}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="store-website">Сайт</Label>
          <Input
            id="store-website"
            value={formState.website}
            onChange={(event) => setFormState((current) => ({ ...current, website: event.target.value }))}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="store-instagram">Instagram</Label>
          <Input
            id="store-instagram"
            value={formState.instagram}
            onChange={(event) => setFormState((current) => ({ ...current, instagram: event.target.value }))}
            placeholder="@stroymir"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="store-bin">БИН</Label>
          <Input
            id="store-bin"
            value={formState.bin_tax_id}
            onChange={(event) => setFormState((current) => ({ ...current, bin_tax_id: event.target.value }))}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="store-director">Руководитель</Label>
          <Input
            id="store-director"
            value={formState.director_name}
            onChange={(event) => setFormState((current) => ({ ...current, director_name: event.target.value }))}
          />
        </div>
        <div className="space-y-2 lg:col-span-2">
          <Label htmlFor="store-logo">Логотип</Label>
          <Input
            ref={logoRef}
            id="store-logo"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(event) => setLogoFile(event.target.files?.[0] ?? null)}
          />
          {logoPreview ? (
            <div className="relative mt-2 h-16 w-40">
              <Image src={logoPreview} alt="Логотип магазина" fill className="object-contain" unoptimized />
            </div>
          ) : null}
        </div>
        <div className="space-y-2 lg:col-span-2">
          <Label htmlFor="store-welcome">Приветственное сообщение (WhatsApp)</Label>
          <textarea
            id="store-welcome"
            rows={4}
            value={formState.welcome_message}
            onChange={(event) => setFormState((current) => ({ ...current, welcome_message: event.target.value }))}
            placeholder={"Здравствуйте!\n\nСпасибо за покупку."}
            className="w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        <div className="space-y-2 lg:col-span-2">
          <Label htmlFor="store-footer">Текст в конце чека</Label>
          <Input
            id="store-footer"
            value={formState.footer_text}
            onChange={(event) => setFormState((current) => ({ ...current, footer_text: event.target.value }))}
            placeholder="Спасибо за покупку!"
          />
        </div>
        <div className="space-y-2 lg:col-span-2">
          <Label htmlFor="store-signature">Подпись</Label>
          <textarea
            id="store-signature"
            rows={3}
            value={formState.receipt_signature}
            onChange={(event) => setFormState((current) => ({ ...current, receipt_signature: event.target.value }))}
            placeholder={"С уважением,\nМагазин «Строй Мир»"}
            className="w-full rounded-2xl border border-input bg-background px-4 py-3 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
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
          <Button type="button" onClick={() => mutation.mutate()} disabled={mutation.isPending || !formState.name.trim()}>
            {mutation.isPending ? "Сохраняем…" : "Сохранить"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
