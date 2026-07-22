"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Bell, ChevronDown, Menu, Search, UserCircle2, X } from "lucide-react";
import { useEffect, useMemo, useState, type ReactElement, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import { LogoutButton } from "@/components/auth/logout-button";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { getNotifications } from "@/lib/platform";
import { getCurrentSession } from "@/lib/session";
import { apiClient } from "@/lib/api-client";
import { clearStoredAuth } from "@/lib/auth";
import { moreLinks, primaryTabs } from "@/components/navigation/nav-config";

function initials(name: string | null | undefined, email: string | undefined): string {
  const source = name?.trim() || email || "KO";
  const parts = source.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0] ?? "K"}${parts[1][0] ?? "O"}`.toUpperCase();
  }
  return source.slice(0, 2).toUpperCase();
}

export function AppShell({ children }: { children: ReactNode }): ReactElement {
  const pathname = usePathname();
  const router = useRouter();
  const [searchValue, setSearchValue] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const sessionQuery = useQuery({
    queryKey: ["session-me"],
    queryFn: getCurrentSession,
  });
  const notificationsQuery = useQuery({
    queryKey: ["platform-notifications-count"],
    queryFn: getNotifications,
  });

  const unreadNotifications = useMemo(
    () => notificationsQuery.data?.items.filter((item) => item.status !== "read").length ?? 0,
    [notificationsQuery.data?.items],
  );

  useEffect(() => {
    const listener = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        const input = document.getElementById("global-search") as HTMLInputElement | null;
        input?.focus();
      }
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    };
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, []);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  const submitSearch = (): void => {
    const query = searchValue.trim();
    if (!query) {
      return;
    }

    const encoded = encodeURIComponent(query);
    if (pathname.startsWith("/products")) {
      router.push(`/products?search=${encoded}`);
    } else if (pathname.startsWith("/ai")) {
      router.push(`/ai/history?search=${encoded}`);
    } else {
      router.push(`/orders?search=${encoded}`);
    }
  };

  const currentTab = primaryTabs.find((item) => item.href === pathname || pathname.startsWith(`${item.href}/`));

  const handleLogout = async (): Promise<void> => {
    if (isLoggingOut) {
      return;
    }

    setIsLoggingOut(true);
    try {
      await apiClient("/auth/logout", { method: "POST" });
    } finally {
      clearStoredAuth();
      router.replace("/login");
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(59,130,246,0.08),transparent_30%),linear-gradient(to_bottom,hsl(var(--background)),hsl(var(--muted)/0.16))]">
      <div className="mx-auto flex min-h-screen max-w-[1600px] flex-col">
        <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur-xl">
          <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-11 rounded-full px-4"
              onClick={() => setMenuOpen(true)}
            >
              <Menu className="h-4 w-4" />
              <span className="font-medium">Kara Orders</span>
            </Button>

            <form
              className="hidden flex-1 items-center gap-2 md:flex"
              onSubmit={(event) => {
                event.preventDefault();
                submitSearch();
              }}
            >
              <div className="relative w-full max-w-2xl">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="global-search"
                  value={searchValue}
                  onChange={(event) => setSearchValue(event.target.value)}
                  placeholder="Поиск заказов, товаров и действий…"
                  className="h-12 rounded-full border-transparent bg-muted/60 pl-11 pr-24 shadow-none"
                />
                <div className="pointer-events-none absolute right-4 top-1/2 hidden -translate-y-1/2 rounded-full border bg-background px-2 py-0.5 text-[11px] font-medium text-muted-foreground md:block">
                  ⌘K
                </div>
              </div>
            </form>

            <div className="ml-auto flex items-center gap-2">
              <Button asChild variant="outline" size="sm" className="hidden h-11 rounded-full px-4 md:inline-flex">
                <Link href="/notifications" className="relative">
                  <Bell className="h-4 w-4" />
                  <span className="sr-only">Уведомления</span>
                  {unreadNotifications > 0 ? (
                    <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-semibold text-primary-foreground">
                      {unreadNotifications > 9 ? "9+" : unreadNotifications}
                    </span>
                  ) : null}
                </Link>
              </Button>
              <div className="hidden items-center gap-3 rounded-full border bg-card px-3 py-2 md:flex">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                  {initials(sessionQuery.data?.user.full_name, sessionQuery.data?.user.email)}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">
                    {sessionQuery.data?.user.full_name ?? sessionQuery.data?.user.email ?? "Профиль"}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">{sessionQuery.data?.company.name ?? "Компания"}</p>
                </div>
                <Button asChild variant="ghost" size="sm" className="h-9 rounded-full px-3">
                  <Link href="/dashboard/company/settings">
                    <ChevronDown className="h-4 w-4" />
                    <span className="sr-only">Настройки компании</span>
                  </Link>
                </Button>
                <LogoutButton />
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 px-4 py-5 pb-24 sm:px-6 lg:px-8 lg:py-8">
          <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-6">{children}</div>
        </main>

        <nav className="sticky bottom-0 z-40 border-t bg-background/95 px-2 py-2 backdrop-blur-xl md:hidden">
          <div className="grid grid-cols-5 gap-1">
            {primaryTabs.map((item) => {
              const active = currentTab?.href === item.href;
              const Icon = item.icon;
              if (item.label === "Ещё") {
                return (
                  <button
                    key={item.href}
                    type="button"
                    onClick={() => setMenuOpen(true)}
                    className={cn(
                      "flex flex-col items-center justify-center gap-1 rounded-2xl px-2 py-3 text-xs font-medium transition-colors",
                      active ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted",
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    {item.label}
                  </button>
                );
              }

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex flex-col items-center justify-center gap-1 rounded-2xl px-2 py-3 text-xs font-medium transition-colors",
                    active ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted",
                  )}
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </nav>
      </div>

      {menuOpen ? (
        <div className="fixed inset-0 z-50 bg-black/40 p-3 sm:p-4" onClick={() => setMenuOpen(false)}>
          <Card
            className="flex h-full w-full max-w-[420px] flex-col rounded-[2rem] p-4 shadow-soft sm:p-5"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4 border-b pb-4">
              <div className="space-y-1">
                <p className="text-sm font-semibold">Kara Orders</p>
                <p className="text-xs text-muted-foreground">Меню навигации</p>
              </div>
              <Button type="button" variant="ghost" size="sm" onClick={() => setMenuOpen(false)}>
                <X className="h-4 w-4" />
                <span className="sr-only">Закрыть меню</span>
              </Button>
            </div>

            <div className="mt-4 flex-1 space-y-2 overflow-y-auto">
              {moreLinks.map((item) => {
                const Icon = item.icon;
                if ("action" in item && item.action === "logout") {
                  return (
                    <Button
                      key={item.label}
                      type="button"
                      variant="outline"
                      className="w-full justify-start rounded-2xl px-4 py-3"
                      onClick={handleLogout}
                      disabled={isLoggingOut}
                    >
                      <Icon className="h-4 w-4 text-muted-foreground" />
                      {isLoggingOut ? "Выход…" : item.label}
                    </Button>
                  );
                }

                const linkItem = item as Extract<Exclude<(typeof moreLinks)[number], { action: "logout" }>, { href: string }>;
                const active = pathname === linkItem.href || pathname.startsWith(`${linkItem.href}/`);
                const content = (
                  <span
                    className={cn(
                      "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-colors",
                      active ? "bg-primary text-primary-foreground" : "hover:bg-muted",
                    )}
                  >
                    <Icon className={cn("h-4 w-4", active ? "text-primary-foreground" : "text-muted-foreground")} />
                    {item.label}
                  </span>
                );

                if (linkItem.external) {
                  return (
                    <a key={linkItem.href} href={linkItem.href} target="_blank" rel="noreferrer">
                      {content}
                    </a>
                  );
                }

                return (
                  <Link key={linkItem.href} href={linkItem.href} onClick={() => setMenuOpen(false)}>
                    {content}
                  </Link>
                );
              })}
            </div>

            <div className="mt-4 rounded-2xl border bg-muted/30 p-4">
              <div className="flex items-center gap-3">
                <UserCircle2 className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">
                    {sessionQuery.data?.user.full_name ?? sessionQuery.data?.user.email ?? "Профиль"}
                  </p>
                  <p className="text-xs text-muted-foreground">{sessionQuery.data?.company.name ?? "Компания"}</p>
                </div>
              </div>
              <div className="mt-4">
                <LogoutButton />
              </div>
            </div>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
