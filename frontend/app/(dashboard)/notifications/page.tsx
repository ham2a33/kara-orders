"use client";

import { Bell, CheckCheck } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ReactElement } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Panel, SectionBadge, formatDate } from "@/components/platform/shared";
import { getNotifications, markNotificationRead } from "@/lib/platform";

export default function NotificationsPage(): ReactElement {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["platform-notifications"], queryFn: getNotifications });

  const markReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["platform-notifications"] });
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <section className="space-y-2">
        <SectionBadge>Уведомления</SectionBadge>
        <h1 className="text-3xl font-semibold tracking-tight">Уведомления компании</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Собирайте предупреждения о trial, лимитах и onboarding-сообщения в одном inbox.
        </p>
      </section>

      <Panel title="Входящие" description="Читайте и архивируйте операционные уведомления.">
        <div className="grid gap-3">
          {query.data?.items.map((notification) => (
            <Card key={notification.id} className="border-muted">
              <CardContent className="flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
                <div className="flex items-start gap-3">
                  <Bell className="mt-0.5 h-5 w-5 text-muted-foreground" />
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-medium">{notification.title}</p>
                      <span className="text-xs uppercase tracking-wide text-muted-foreground">{notification.status}</span>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">{notification.message}</p>
                    <p className="mt-2 text-xs text-muted-foreground">{formatDate(notification.created_at)}</p>
                  </div>
                </div>
                {notification.status !== "read" ? (
                    <Button
                      type="button"
                      variant="outline"
                      disabled={markReadMutation.isPending}
                      onClick={() => markReadMutation.mutate(notification.id)}
                    >
                      <CheckCheck className="h-4 w-4" />
                    Отметить прочитанным
                    </Button>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      </Panel>
    </div>
  );
}
