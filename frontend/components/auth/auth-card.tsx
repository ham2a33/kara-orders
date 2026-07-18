"use client";

import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type AuthCardProps = {
  badge: string;
  title: string;
  description: string;
  children: ReactNode;
};

export function AuthCard({ badge, title, description, children }: AuthCardProps) {
  return (
    <div className="grid w-full gap-8 lg:grid-cols-[1fr_0.9fr]">
      <section className="space-y-6">
        <Badge>{badge}</Badge>
        <div className="space-y-3">
          <h1 className="text-4xl font-semibold tracking-tight">{title}</h1>
          <p className="max-w-xl text-lg text-muted-foreground">{description}</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Production-ready auth</CardTitle>
            <CardDescription>JWT access tokens, HTTP-only refresh cookies, validation, and tenant-aware redirects.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border bg-muted/40 p-4">
              <p className="text-sm font-medium">Secure session flow</p>
              <p className="text-sm text-muted-foreground">Access tokens power the dashboard; refresh cookies keep sessions alive.</p>
            </div>
            <div className="rounded-2xl border bg-muted/40 p-4">
              <p className="text-sm font-medium">Backend validation</p>
              <p className="text-sm text-muted-foreground">API errors surface directly on the form for fast correction.</p>
            </div>
          </CardContent>
        </Card>
      </section>

      <Card className="max-w-xl lg:justify-self-end">
        {children}
      </Card>
    </div>
  );
}
