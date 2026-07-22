import type { ReactElement, ReactNode } from "react";

import { AppShell } from "@/components/navigation/app-shell";

export default function DashboardLayout({ children }: { children: ReactNode }): ReactElement {
  return <AppShell>{children}</AppShell>;
}
