import { Suspense, type ReactElement } from "react";

import { Card, CardContent, CardHeader } from "@/components/ui/card";

import { NewProductPageClient } from "./new-product-page-client";

function NewProductPageFallback(): ReactElement {
  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <div className="h-6 w-24 animate-pulse rounded-full bg-muted" />
        <div className="h-9 w-64 animate-pulse rounded-2xl bg-muted" />
        <div className="h-5 w-full max-w-2xl animate-pulse rounded-full bg-muted" />
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <div className="h-6 w-40 animate-pulse rounded-full bg-muted" />
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="h-11 animate-pulse rounded-2xl bg-muted md:col-span-2" />
            <div className="h-11 animate-pulse rounded-2xl bg-muted md:col-span-2" />
            <div className="h-11 animate-pulse rounded-2xl bg-muted" />
            <div className="h-11 animate-pulse rounded-2xl bg-muted" />
            <div className="h-11 animate-pulse rounded-2xl bg-muted" />
            <div className="h-11 animate-pulse rounded-2xl bg-muted" />
            <div className="h-11 animate-pulse rounded-2xl bg-muted" />
            <div className="h-11 animate-pulse rounded-2xl bg-muted" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="h-6 w-40 animate-pulse rounded-full bg-muted" />
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="h-11 animate-pulse rounded-2xl bg-muted" />
            <div className="h-11 animate-pulse rounded-2xl bg-muted" />
            <div className="h-11 animate-pulse rounded-2xl bg-muted" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function NewProductPage(): ReactElement {
  return (
    <Suspense fallback={<NewProductPageFallback />}>
      <NewProductPageClient />
    </Suspense>
  );
}
