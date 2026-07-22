import {
  Activity,
  BarChart3,
  Bell,
  Boxes,
  Building2,
  Home,
  LogOut,
  Menu,
  Package,
  ReceiptText,
  Settings2,
  Sparkles,
  Wallet,
  type LucideIcon,
} from "lucide-react";

export type NavLinkItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  external?: boolean;
};

export type DrawerLinkItem =
  | {
      href: string;
      label: string;
      icon: LucideIcon;
      external?: boolean;
    }
  | {
      action: "logout";
      label: string;
      icon: LucideIcon;
    };

export const primaryTabs: NavLinkItem[] = [
  { href: "/dashboard", label: "Главная", icon: Home },
  { href: "/orders", label: "Заказы", icon: ReceiptText },
  { href: "/products", label: "Каталог", icon: Package },
  { href: "/ai", label: "ИИ", icon: Sparkles },
  { href: "/more", label: "Ещё", icon: Menu },
];

export const quickActions: NavLinkItem[] = [
  { href: "/orders/new", label: "Новый заказ", icon: ReceiptText },
  { href: "/products/new", label: "Добавить товар", icon: Package },
  { href: "/ai", label: "Распознать чек", icon: Sparkles },
];

export const moreLinks: DrawerLinkItem[] = [
  { href: "/dashboard", label: "Главная", icon: Home },
  { href: "/orders/new", label: "Новый заказ", icon: ReceiptText },
  { href: "/products", label: "Каталог товаров", icon: Package },
  { href: "/products/inventory", label: "Склад", icon: Boxes },
  { href: "/orders", label: "Заказы", icon: ReceiptText },
  { href: "/ai", label: "AI Распознавание", icon: Sparkles },
  { href: "/settings", label: "Настройки", icon: Settings2 },
  { action: "logout", label: "Выход", icon: LogOut },
];

export const dashboardSections: Array<{ href: string; label: string; icon: LucideIcon }> = [
  { href: "/dashboard/company", label: "Компания", icon: Building2 },
  { href: "/subscription", label: "Подписка", icon: Wallet },
  { href: "/orders", label: "Заказы", icon: ReceiptText },
  { href: "/products", label: "Каталог", icon: Boxes },
  { href: "/ai", label: "ИИ", icon: Sparkles },
  { href: "/analytics", label: "Аналитика", icon: BarChart3 },
  { href: "/reports", label: "Отчёты", icon: Activity },
  { href: "/notifications", label: "Уведомления", icon: Bell },
  { href: "/system-settings", label: "Системные настройки", icon: Settings2 },
];
