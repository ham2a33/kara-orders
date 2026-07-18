"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement, ReactNode } from "react";

import { createQueryClient } from "@/lib/query-client";

const queryClient = createQueryClient();

export default function Providers({ children }: { children: ReactNode }): ReactElement {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

