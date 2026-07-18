import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactElement, ReactNode } from "react";

import { AUTH_COOKIE_NAMES } from "@/lib/auth";

export default async function AuthLayout({ children }: { children: ReactNode }): Promise<ReactElement> {
  const accessToken = (await cookies()).get(AUTH_COOKIE_NAMES.accessToken);
  if (accessToken) {
    redirect("/dashboard");
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-background via-background to-muted/30">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl items-center px-6 py-12 lg:px-10">{children}</div>
    </main>
  );
}
