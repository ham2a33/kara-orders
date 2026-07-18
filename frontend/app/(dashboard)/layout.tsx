import Link from "next/link";
import type { ReactElement, ReactNode } from "react";

import { LogoutButton } from "@/components/auth/logout-button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

const navigation = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/company", label: "Company Profile" },
  { href: "/dashboard/company/settings", label: "Company Settings" },
  { href: "/dashboard/company/branding", label: "Branding" },
  { href: "/dashboard/company/invoice-settings", label: "Invoice Settings" },
  { href: "/dashboard/company/users", label: "User Management" },
  { href: "/subscription", label: "Subscription" },
  { href: "/usage", label: "Usage" },
  { href: "/billing", label: "Billing" },
  { href: "/admin", label: "Admin" },
  { href: "/audit", label: "Audit Logs" },
  { href: "/notifications", label: "Notifications" },
  { href: "/system-settings", label: "System Settings" },
  { href: "/products", label: "Products" },
  { href: "/orders", label: "Orders" },
  { href: "/ai", label: "AI" },
  { href: "/analytics", label: "Analytics" },
  { href: "/reports", label: "Reports" },
];

export default function DashboardLayout({ children }: { children: ReactNode }): ReactElement {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="mx-auto grid min-h-screen max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[260px_1fr] lg:px-8">
        <aside className="flex flex-col gap-6">
          <Card className="p-5">
            <Badge className="mb-3">Kara Orders</Badge>
            <h1 className="text-lg font-semibold">SaaS workspace</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Navigation for company, product, order, analytics, and platform modules.
            </p>
          </Card>
          <nav className="grid gap-2">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-2xl border bg-card px-4 py-3 text-sm font-medium text-foreground transition-colors hover:bg-muted"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <LogoutButton />
        </aside>
        <main className="flex flex-col gap-6">{children}</main>
      </div>
    </div>
  );
}
