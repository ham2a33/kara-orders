import {
  Activity,
  BarChart3,
  Bell,
  Boxes,
  Building2,
  FileText,
  Globe,
  Home,
  Menu,
  Package,
  ReceiptText,
  Settings2,
  ShieldCheck,
  Sparkles,
  Store,
  Users,
  Wallet,
  type LucideIcon,
} from "lucide-react";

export type NavLinkItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  external?: boolean;
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

export const moreLinks: NavLinkItem[] = [
  { href: "/settings", label: "Настройки", icon: Settings2 },
  { href: "/dashboard/company", label: "Компания", icon: Building2 },
  { href: "/subscription", label: "Подписка", icon: Wallet },
  { href: "/dashboard/company/users", label: "Сотрудники", icon: Users },
  { href: "/dashboard/company/settings", label: "Профиль", icon: Store },
  { href: "/billing", label: "Биллинг", icon: Wallet },
  { href: "/reports", label: "Отчёты", icon: BarChart3 },
  { href: "/system-settings", label: "Интеграции", icon: Globe },
  { href: "/notifications", label: "Уведомления", icon: Bell },
  { href: "http://localhost:8000/docs", label: "API", icon: FileText, external: true },
  { href: "/audit", label: "Аудит", icon: ShieldCheck },
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
