"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Bell, Search, ChevronDown, Menu, UserCircle2 } from "lucide-react";
import { useEffect, useMemo, useState, type ReactElement, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import { LogoutButton } from "@/components/auth/logout-button";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { getNotifications } from "@/lib/platform";
import { getCurrentSession } from "@/lib/session";
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
  const [moreOpen, setMoreOpen] = useState(false);

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
        setMoreOpen(false);
      }
    };
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, []);

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

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(59,130,246,0.08),transparent_30%),linear-gradient(to_bottom,hsl(var(--background)),hsl(var(--muted)/0.16))]">
      <div className="mx-auto flex min-h-screen max-w-[1600px] flex-col">
        <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur-xl">
          <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
            <Link href="/dashboard" className="flex items-center gap-3 rounded-2xl px-2 py-1 transition-colors hover:bg-muted">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-sm font-semibold text-primary-foreground shadow-soft">
                KO
              </div>
              <div className="hidden flex-col leading-tight sm:flex">
                <span className="text-sm font-semibold">Kara Orders</span>
                <span className="text-xs text-muted-foreground">Премиум-панель управления</span>
              </div>
            </Link>

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
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-11 rounded-full px-4 md:hidden"
                onClick={() => setMoreOpen(true)}
                aria-label="Открыть дополнительное меню"
              >
                <Menu className="h-4 w-4" />
                <span className="sr-only">Открыть дополнительное меню</span>
              </Button>
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
                    onClick={() => setMoreOpen(true)}
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

      {moreOpen ? (
        <div className="fixed inset-0 z-50 bg-black/40 p-4 md:hidden" onClick={() => setMoreOpen(false)}>
          <Card className="mx-auto mt-auto max-w-md rounded-[2rem] p-5 shadow-soft" onClick={(event) => event.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold">Ещё</p>
                <p className="text-xs text-muted-foreground">Вспомогательные разделы</p>
              </div>
              <Button type="button" variant="ghost" size="sm" onClick={() => setMoreOpen(false)}>
                Закрыть
              </Button>
            </div>
            <div className="grid gap-2">
              {moreLinks.map((item) => {
                const Icon = item.icon;
                const content = (
                  <span className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-colors hover:bg-muted">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    {item.label}
                  </span>
                );
                return item.external ? (
                  <a key={item.href} href={item.href} target="_blank" rel="noreferrer">
                    {content}
                  </a>
                ) : (
                  <Link key={item.href} href={item.href} onClick={() => setMoreOpen(false)}>
                    {content}
                  </Link>
                );
              })}
            </div>
            <div className="mt-5 rounded-2xl border bg-muted/30 p-4">
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
