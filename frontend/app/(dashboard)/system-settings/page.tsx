"use client";

import { Save, Wrench } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type ReactElement } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Panel, SectionBadge, formatDate } from "@/components/platform/shared";
import { getSystemSettings, updateSystemSettings } from "@/lib/platform";

export default function SystemSettingsPage(): ReactElement {
  const queryClient = useQueryClient();
  const settingsQuery = useQuery({
    queryKey: ["platform-system-settings"],
    queryFn: getSystemSettings,
  });

  const mutation = useMutation({
    mutationFn: updateSystemSettings,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["platform-system-settings"] });
    },
  });

  const [formState, setFormState] = useState({
    ai_enabled: settingsQuery.data?.ai_enabled ?? true,
    maintenance_mode: settingsQuery.data?.maintenance_mode ?? false,
    max_upload_size_mb: settingsQuery.data?.max_upload_size_mb ?? 20,
    allowed_file_types: (settingsQuery.data?.allowed_file_types ?? ["pdf", "png", "jpg", "jpeg", "csv", "xlsx"]).join(", "),
    default_currency: settingsQuery.data?.default_currency ?? "KZT",
    default_tax: settingsQuery.data?.default_tax ?? "0",
    notes: settingsQuery.data?.notes ?? "",
  });

  const settings = settingsQuery.data;

  useEffect(() => {
    if (!settings) {
      return;
    }
    setFormState({
      ai_enabled: settings.ai_enabled,
      maintenance_mode: settings.maintenance_mode,
      max_upload_size_mb: settings.max_upload_size_mb,
      allowed_file_types: settings.allowed_file_types.join(", "),
      default_currency: settings.default_currency,
      default_tax: settings.default_tax,
      notes: settings.notes ?? "",
    });
  }, [settings]);

  const submit = (): void => {
    mutation.mutate({
      ai_enabled: formState.ai_enabled,
      maintenance_mode: formState.maintenance_mode,
      max_upload_size_mb: Number(formState.max_upload_size_mb),
      allowed_file_types: formState.allowed_file_types
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      default_currency: formState.default_currency,
      default_tax: String(formState.default_tax),
      notes: formState.notes,
    });
  };

  return (
    <div className="flex flex-col gap-6">
      <section className="space-y-2">
        <SectionBadge>Системные настройки</SectionBadge>
        <h1 className="text-3xl font-semibold tracking-tight">Глобальные настройки платформы</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Управляйте доступностью AI, режимом обслуживания, загрузками и глобальными настройками из одного экрана администратора.
        </p>
      </section>

      <Card>
        <CardContent className="grid gap-4 p-5 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <p className="text-sm text-muted-foreground">AI включён</p>
            <p className="mt-1 text-lg font-semibold">{settings?.ai_enabled ? "Да" : "Нет"}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Режим обслуживания</p>
            <p className="mt-1 text-lg font-semibold">{settings?.maintenance_mode ? "Включён" : "Выключен"}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Лимит загрузки</p>
            <p className="mt-1 text-lg font-semibold">{settings?.max_upload_size_mb ?? "—"} MB</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Последнее обновление</p>
            <p className="mt-1 text-lg font-semibold">{formatDate(settings?.updated_at ?? null)}</p>
          </div>
        </CardContent>
      </Card>

      <Panel title="Редактируемые настройки" description="Все изменения проверяются на сервере и попадают в аудит.">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="grid gap-2 text-sm">
            <span className="text-muted-foreground">AI включён</span>
            <select
              value={String(formState.ai_enabled)}
              onChange={(event) =>
                setFormState((current) => ({ ...current, ai_enabled: event.target.value === "true" }))
              }
              className="h-11 rounded-xl border bg-background px-3"
            >
              <option value="true">Включён</option>
              <option value="false">Выключен</option>
            </select>
          </label>
          <label className="grid gap-2 text-sm">
            <span className="text-muted-foreground">Режим обслуживания</span>
            <select
              value={String(formState.maintenance_mode)}
              onChange={(event) =>
                setFormState((current) => ({ ...current, maintenance_mode: event.target.value === "true" }))
              }
              className="h-11 rounded-xl border bg-background px-3"
            >
              <option value="false">Выключен</option>
              <option value="true">Включён</option>
            </select>
          </label>
          <label className="grid gap-2 text-sm">
            <span className="text-muted-foreground">Макс. размер загрузки, МБ</span>
            <input
              type="number"
              value={formState.max_upload_size_mb}
              onChange={(event) =>
                setFormState((current) => ({ ...current, max_upload_size_mb: Number(event.target.value) }))
              }
              className="h-11 rounded-xl border bg-background px-3"
            />
          </label>
          <label className="grid gap-2 text-sm">
            <span className="text-muted-foreground">Валюта по умолчанию</span>
            <input
              value={formState.default_currency}
              onChange={(event) =>
                setFormState((current) => ({ ...current, default_currency: event.target.value.toUpperCase() }))
              }
              className="h-11 rounded-xl border bg-background px-3"
            />
          </label>
          <label className="grid gap-2 text-sm">
            <span className="text-muted-foreground">Налог по умолчанию</span>
            <input
              type="number"
              step="0.01"
              value={formState.default_tax}
              onChange={(event) => setFormState((current) => ({ ...current, default_tax: event.target.value }))}
              className="h-11 rounded-xl border bg-background px-3"
            />
          </label>
          <label className="grid gap-2 text-sm">
            <span className="text-muted-foreground">Разрешённые типы файлов</span>
            <input
              value={formState.allowed_file_types}
              onChange={(event) =>
                setFormState((current) => ({ ...current, allowed_file_types: event.target.value }))
              }
              className="h-11 rounded-xl border bg-background px-3"
            />
          </label>
          <label className="grid gap-2 text-sm md:col-span-2">
            <span className="text-muted-foreground">Заметки</span>
            <textarea
              value={formState.notes}
              onChange={(event) => setFormState((current) => ({ ...current, notes: event.target.value }))}
              className="min-h-28 rounded-2xl border bg-background px-3 py-3"
            />
          </label>
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <Button type="button" onClick={submit} disabled={mutation.isPending}>
            <Save className="h-4 w-4" />
            Сохранить изменения
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() =>
              setFormState({
                ai_enabled: settings?.ai_enabled ?? true,
                maintenance_mode: settings?.maintenance_mode ?? false,
                max_upload_size_mb: settings?.max_upload_size_mb ?? 20,
                allowed_file_types: (settings?.allowed_file_types ?? ["pdf", "png", "jpg", "jpeg", "csv", "xlsx"]).join(", "),
                default_currency: settings?.default_currency ?? "KZT",
                default_tax: settings?.default_tax ?? "0",
                notes: settings?.notes ?? "",
              })
            }
          >
            <Wrench className="h-4 w-4" />
            Сбросить форму
          </Button>
        </div>
      </Panel>
    </div>
  );
}
