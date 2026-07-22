"use client";

import { useMemo, useState, type ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  changeCompanyUserRole,
  getCompanyInvitations,
  getCompanyUsers,
  inviteCompanyUser,
  removeCompanyUser,
} from "@/lib/company";
import { extractErrorMessage } from "@/lib/errors";
import type { CompanyRole } from "@/types/company";

const roleLabels: Record<CompanyRole, string> = {
  owner: "Владелец",
  admin: "Администратор",
  manager: "Менеджер",
  employee: "Сотрудник",
};

export default function CompanyUsersPage(): ReactElement {
  const queryClient = useQueryClient();
  const usersQuery = useQuery({
    queryKey: ["company-users"],
    queryFn: getCompanyUsers,
  });
  const invitationsQuery = useQuery({
    queryKey: ["company-invitations"],
    queryFn: getCompanyInvitations,
  });

  const [inviteForm, setInviteForm] = useState({
    email: "",
    full_name: "",
    role: "employee" as Exclude<CompanyRole, "owner">,
  });
  const [roleDrafts, setRoleDrafts] = useState<Record<string, CompanyRole>>({});
  const [message, setMessage] = useState<string | null>(null);

  const users = usersQuery.data?.items ?? [];
  const invitations = invitationsQuery.data?.items ?? [];

  const inviteMutation = useMutation({
    mutationFn: inviteCompanyUser,
    onSuccess: async () => {
      setInviteForm({ email: "", full_name: "", role: "employee" });
      setMessage("Приглашение отправлено.");
      await queryClient.invalidateQueries({ queryKey: ["company-users"] });
      await queryClient.invalidateQueries({ queryKey: ["company-invitations"] });
    },
  });

  const roleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: CompanyRole }) => changeCompanyUserRole(userId, role),
    onSuccess: async () => {
      setMessage("Роль пользователя обновлена.");
      await queryClient.invalidateQueries({ queryKey: ["company-users"] });
    },
  });

  const removeMutation = useMutation({
    mutationFn: removeCompanyUser,
    onSuccess: async () => {
      setMessage("Пользователь удалён из компании.");
      await queryClient.invalidateQueries({ queryKey: ["company-users"] });
    },
  });

  const inviterCount = useMemo(() => invitations.length, [invitations.length]);

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_0.8fr]">
      <Card>
        <CardHeader>
          <Badge className="w-fit">Пользователи</Badge>
          <CardTitle>Приглашайте и управляйте сотрудниками</CardTitle>
          <CardDescription>Владелец и администратор могут назначать доступ, не покидая рабочее пространство.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          {users.map((member) => {
            const currentRole = roleDrafts[member.id] ?? member.role;
            const canEdit = member.role !== "owner";
            return (
              <div
                key={member.email}
                className="flex flex-col gap-4 rounded-2xl border bg-muted/30 p-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="font-medium">{member.full_name ?? member.email}</p>
                  <p className="text-sm text-muted-foreground">{member.email}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    В компании с {new Date(member.created_at).toLocaleDateString("ru-RU")}
                  </p>
                </div>
                <div className="flex flex-col gap-3 sm:items-end">
                  <Badge variant="success" className="w-fit">
                    {roleLabels[member.role]}
                  </Badge>
                  {canEdit ? (
                    <div className="flex flex-wrap gap-2">
                      <select
                        value={currentRole}
                        onChange={(event) =>
                          setRoleDrafts((current) => ({
                            ...current,
                            [member.id]: event.target.value as CompanyRole,
                          }))
                        }
                        className="h-11 rounded-xl border bg-background px-3 text-sm"
                      >
                        <option value="admin">Администратор</option>
                        <option value="manager">Менеджер</option>
                        <option value="employee">Сотрудник</option>
                      </select>
                      <Button
                        type="button"
                        variant="outline"
                        disabled={roleMutation.isPending || currentRole === member.role}
                        onClick={() => roleMutation.mutate({ userId: member.id, role: currentRole })}
                      >
                        Обновить роль
                      </Button>
                      {member.role !== "owner" ? (
                        <Button
                          type="button"
                          variant="secondary"
                          disabled={removeMutation.isPending}
                          onClick={() => removeMutation.mutate(member.id)}
                        >
                          Удалить
                        </Button>
                      ) : null}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">Роль владельца изменить нельзя.</p>
                  )}
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Пригласить пользователя</CardTitle>
          <CardDescription>Создайте новое приглашение для коллеги.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="inviteEmail">Эл. почта</Label>
            <Input
              id="inviteEmail"
              type="email"
              placeholder="employee@company.com"
              value={inviteForm.email}
              onChange={(event) => setInviteForm((current) => ({ ...current, email: event.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="inviteName">Полное имя</Label>
            <Input
              id="inviteName"
              placeholder="Имя сотрудника"
              value={inviteForm.full_name}
              onChange={(event) => setInviteForm((current) => ({ ...current, full_name: event.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="inviteRole">Роль</Label>
            <select
              id="inviteRole"
              className="flex h-11 w-full rounded-2xl border border-input bg-background px-4 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
              value={inviteForm.role}
              onChange={(event) =>
                setInviteForm((current) => ({ ...current, role: event.target.value as Exclude<CompanyRole, "owner"> }))
              }
            >
              <option value="admin">Администратор</option>
              <option value="manager">Менеджер</option>
              <option value="employee">Сотрудник</option>
            </select>
          </div>
          {message ? (
            <p className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-300">
              {message}
            </p>
          ) : null}
          {inviteMutation.isError || roleMutation.isError || removeMutation.isError ? (
            <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {extractErrorMessage(inviteMutation.error ?? roleMutation.error ?? removeMutation.error)}
            </p>
          ) : null}
          <Button
            className="w-full"
            type="button"
            disabled={inviteMutation.isPending}
            onClick={() => {
              setMessage(null);
              inviteMutation.mutate({
                email: inviteForm.email.trim(),
                full_name: inviteForm.full_name.trim() || null,
                role: inviteForm.role,
              });
            }}
          >
            {inviteMutation.isPending ? "Отправляем..." : "Отправить приглашение"}
          </Button>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">Ожидающие приглашения</p>
              <Badge variant="outline">{inviterCount}</Badge>
            </div>
            {invitations.map((invitation) => (
              <div key={invitation.id} className="rounded-2xl border bg-muted/30 p-4 text-sm">
                <p className="font-medium">{invitation.email}</p>
                <p className="text-muted-foreground">
                  {roleLabels[invitation.role]} • Истекает {new Date(invitation.expires_at).toLocaleDateString("ru-RU")}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
