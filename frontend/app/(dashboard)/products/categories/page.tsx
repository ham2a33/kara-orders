"use client";

import { useMemo, useState, type ReactElement } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createCategory, getCategories } from "@/lib/products";
import { extractErrorMessage } from "@/lib/errors";

function flattenCategories(nodes: Awaited<ReturnType<typeof getCategories>>["items"]): Array<{
  id: string;
  name: string;
  slug: string;
  depth: string;
  count: number;
}> {
  const rows: Array<{ id: string; name: string; slug: string; depth: string; count: number }> = [];
  const walk = (items: typeof nodes, prefix: string[] = []) => {
    for (const item of items) {
      rows.push({
        id: item.id,
        name: item.name,
        slug: item.slug,
        depth: [...prefix, item.name].join(" / "),
        count: item.product_count,
      });
      if (item.children.length > 0) {
        walk(item.children, [...prefix, item.name]);
      }
    }
  };
  walk(nodes);
  return rows;
}

export default function ProductCategoriesPage(): ReactElement {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const categoriesQuery = useQuery({
    queryKey: ["product-categories"],
    queryFn: getCategories,
  });
  const categories = useMemo(() => flattenCategories(categoriesQuery.data?.items ?? []), [categoriesQuery.data]);
  const filteredCategories = categories.filter((category) =>
    `${category.name} ${category.slug} ${category.depth}`.toLowerCase().includes(search.toLowerCase()),
  );

  const mutation = useMutation({
    mutationFn: createCategory,
    onSuccess: async () => {
      setName("");
      setSlug("");
      await queryClient.invalidateQueries({ queryKey: ["product-categories"] });
    },
  });

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <Badge>Categories</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Category tree</h1>
        <p className="max-w-2xl text-muted-foreground">
          Organize products with nested categories, product counts, and a fast search surface.
        </p>
      </section>

      <Card>
        <CardHeader className="gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle>Search categories</CardTitle>
            <CardDescription>Designed to scale across broad and deeply nested catalog trees.</CardDescription>
          </div>
          <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto]">
            <Input className="w-full md:w-64" placeholder="Search categories" value={search} onChange={(event) => setSearch(event.target.value)} />
            <Input placeholder="Category name" value={name} onChange={(event) => setName(event.target.value)} />
            <Button
              type="button"
              disabled={mutation.isPending || name.trim().length === 0 || slug.trim().length === 0}
              onClick={() =>
                mutation.mutate({
                  name: name.trim(),
                  slug: slug.trim(),
                })
              }
            >
              Add category
            </Button>
            <Input placeholder="Category slug" value={slug} onChange={(event) => setSlug(event.target.value)} />
          </div>
        </CardHeader>
        <CardContent className="grid gap-3">
          {mutation.isError ? (
            <p className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {extractErrorMessage(mutation.error)}
            </p>
          ) : null}
          {filteredCategories.map((category) => (
            <div key={category.id} className="flex items-center justify-between rounded-2xl border px-4 py-3">
              <div>
                <p className="font-medium">{category.name}</p>
                <p className="text-sm text-muted-foreground">{category.depth}</p>
              </div>
              <Badge variant="success">{category.count} products</Badge>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
