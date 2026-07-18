"use client";

import Link from "next/link";
import { useMemo, useState, type ReactElement } from "react";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getAIRecognitions } from "@/lib/ai";

export default function AiHistoryPage(): ReactElement {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [inputType, setInputType] = useState("");
  const query = useQuery({
    queryKey: ["ai-history", search, status, inputType],
    queryFn: () =>
      getAIRecognitions({
        search: search || undefined,
        status: status || undefined,
        inputType: inputType || undefined,
        pageSize: 20,
      }),
  });

  const count = useMemo(() => query.data?.total ?? 0, [query.data?.total]);

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <Badge>AI history</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">Recognition history</h1>
        <p className="max-w-2xl text-muted-foreground">
          Review past extractions, confidence scores, and which recognitions were converted into orders.
        </p>
      </section>

      <Card>
        <CardHeader className="gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle>Latest recognition runs</CardTitle>
            <CardDescription>Search, filter, and inspect the AI audit trail.</CardDescription>
          </div>
          <div className="flex gap-3">
            <Button asChild variant="outline">
              <Link href="/ai">New recognition</Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <Input placeholder="Search recognitions" value={search} onChange={(event) => setSearch(event.target.value)} />
          <select
            className="h-11 rounded-xl border bg-background px-3 text-sm"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">All statuses</option>
            <option value="completed">Completed</option>
            <option value="needs_review">Needs review</option>
            <option value="failed">Failed</option>
            <option value="converted">Converted</option>
          </select>
          <select
            className="h-11 rounded-xl border bg-background px-3 text-sm"
            value={inputType}
            onChange={(event) => setInputType(event.target.value)}
          >
            <option value="">All input types</option>
            <option value="photo">Photo</option>
            <option value="voice">Voice</option>
            <option value="text">Text</option>
            <option value="pdf">PDF</option>
          </select>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="overflow-hidden p-0">
          <div className="border-b px-6 py-4">
            <p className="text-sm text-muted-foreground">Total recognitions: {count}</p>
          </div>
          <div className="overflow-x-auto p-6">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b text-muted-foreground">
                <tr>
                  <th className="py-3 pr-4 font-medium">ID</th>
                  <th className="py-3 pr-4 font-medium">Source</th>
                  <th className="py-3 pr-4 font-medium">Status</th>
                  <th className="py-3 pr-4 font-medium">Confidence</th>
                  <th className="py-3 pr-4 font-medium">Order</th>
                  <th className="py-3 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {(query.data?.items ?? []).map((item) => (
                  <tr key={item.id} className="border-b last:border-0">
                    <td className="py-4 pr-4 font-medium">{item.id}</td>
                    <td className="py-4 pr-4 text-muted-foreground">{item.input_type}</td>
                    <td className="py-4 pr-4">
                      <Badge
                        variant={
                          item.status === "converted"
                            ? "success"
                            : item.status === "needs_review"
                              ? "warning"
                              : item.status === "failed"
                                ? "danger"
                                : "default"
                        }
                      >
                        {item.status}
                      </Badge>
                    </td>
                    <td className="py-4 pr-4 text-muted-foreground">{item.confidence ?? "—"}</td>
                    <td className="py-4 pr-4 text-muted-foreground">{item.created_order_id ?? "—"}</td>
                    <td className="py-4">
                      <Button asChild size="sm" variant="secondary">
                        <Link href={`/ai/review/${item.id}`}>Review</Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
