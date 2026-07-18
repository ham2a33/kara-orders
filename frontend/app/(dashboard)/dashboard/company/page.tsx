"use client";

import Link from "next/link";
import type { ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getCompanyUsers, getMyCompany } from "@/lib/company";
import { formatDate, formatCount } from "@/components/platform/shared";
import { extractErrorMessage } from "@/lib/errors";

export default function CompanyProfilePage(): ReactElement {
  const companyQuery = useQuery({
    queryKey: ["company-profile"],
    queryFn: getMyCompany,
  });

  const usersQuery = useQuery({
    queryKey: ["company-users"],
    queryFn: getCompanyUsers,
  });

  const company = companyQuery.data;
  const activeUsers = usersQuery.data?.items.filter((user) => user.is_active && !user.deleted_at).length ?? 0;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <Badge className="w-fit">Company Profile</Badge>
          <CardTitle>{company?.name ?? "Company profile"}</CardTitle>
          <CardDescription>
            Keep the business profile, branding, and invoice defaults aligned with how the team actually works.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border bg-muted/40 p-4">
            <p className="text-sm text-muted-foreground">Active users</p>
            <p className="mt-2 text-2xl font-semibold">{formatCount(activeUsers)}</p>
          </div>
          <div className="rounded-2xl border bg-muted/40 p-4">
            <p className="text-sm text-muted-foreground">Currency</p>
            <p className="mt-2 text-2xl font-semibold">{company?.currency ?? "—"}</p>
          </div>
          <div className="rounded-2xl border bg-muted/40 p-4">
            <p className="text-sm text-muted-foreground">Updated</p>
            <p className="mt-2 text-2xl font-semibold">{formatDate(company?.updated_at ?? null)}</p>
          </div>
        </CardContent>
      </Card>

      {companyQuery.isError ? (
        <Card className="border-destructive/30">
          <CardContent className="p-5 text-sm text-destructive">
            {extractErrorMessage(companyQuery.error)}
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
        <Card>
          <CardHeader>
            <CardTitle>Company snapshot</CardTitle>
            <CardDescription>Overview data used across invoices, orders, and user invitations.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            {[
              ["Company name", company?.name ?? "—"],
              ["Email", company?.email ?? "—"],
              ["Phone", company?.phone ?? "—"],
              ["Website", company?.website ?? "—"],
              ["Timezone", company?.timezone ?? "—"],
              ["Language", company?.language ?? "—"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl border bg-muted/30 p-4">
                <p className="text-sm text-muted-foreground">{label}</p>
                <p className="mt-1 text-sm font-medium">{value}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick actions</CardTitle>
            <CardDescription>Jump into the dedicated company management screens.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            <Button asChild className="justify-start">
              <Link href="/dashboard/company/settings">Open settings</Link>
            </Button>
            <Button asChild variant="outline" className="justify-start">
              <Link href="/dashboard/company/branding">Branding</Link>
            </Button>
            <Button asChild variant="outline" className="justify-start">
              <Link href="/dashboard/company/invoice-settings">Invoice settings</Link>
            </Button>
            <Button asChild variant="outline" className="justify-start">
              <Link href="/dashboard/company/users">User management</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
