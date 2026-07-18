"use client";

import { useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Panel, SectionBadge, formatDate } from "@/components/platform/shared";
import { getAuditLogs } from "@/lib/platform";

export default function AuditPage(): ReactElement {
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);
  const query = useQuery({
    queryKey: ["platform-audit", page, action],
    queryFn: () => getAuditLogs({ page, pageSize: 20, action: action || undefined }),
  });

  const logs = query.data?.items ?? [];

  return (
    <div className="flex flex-col gap-6">
      <section className="space-y-2">
        <SectionBadge>Audit Logs</SectionBadge>
        <h1 className="text-3xl font-semibold tracking-tight">Operational audit trail</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Track authentication, role changes, company changes, AI requests, orders, and product updates.
        </p>
      </section>

      <Card>
        <CardContent className="grid gap-4 p-5 md:grid-cols-[1fr_auto]">
          <label className="grid gap-2 text-sm">
            <span className="text-muted-foreground">Action filter</span>
            <input
              value={action}
              onChange={(event) => setAction(event.target.value)}
              placeholder="login, role_changed, order_created..."
              className="h-11 rounded-xl border bg-background px-3"
            />
          </label>
          <div className="flex items-end">
            <Button type="button" variant="outline" onClick={() => setPage(1)}>
              Apply filter
            </Button>
          </div>
        </CardContent>
      </Card>

      <Panel title="Recent activity" description="Server-side audit logs with company isolation.">
        <div className="grid gap-3">
          {logs.map((log) => (
            <div key={log.id} className="rounded-2xl border bg-muted/20 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium">{log.action}</p>
                    <Badge variant="outline">{log.resource_type ?? "system"}</Badge>
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {log.description ?? "No description"} • {formatDate(log.created_at)}
                  </p>
                </div>
                <div className="text-right text-xs text-muted-foreground">
                  <p>{log.resource_id ?? "—"}</p>
                  <p>{log.actor_user_id ?? "system"}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Page {query.data?.page ?? page} of {Math.max(Math.ceil((query.data?.total ?? 0) / 20), 1)}
          </p>
          <div className="flex gap-2">
            <Button type="button" variant="outline" disabled={page <= 1} onClick={() => setPage((current) => Math.max(current - 1, 1))}>
              Previous
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={(query.data?.total ?? 0) <= page * 20}
              onClick={() => setPage((current) => current + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      </Panel>
    </div>
  );
}
