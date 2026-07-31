import Link from "next/link";
import type { ReactElement } from "react";

import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const settingsLinks = [
  {
    href: "/settings/store",
    title: "Информация магазина",
    description: "Реквизиты, контакты, приветствие и подпись для чеков и WhatsApp.",
  },
  {
    href: "/dashboard/company/settings",
    title: "Реквизиты компании",
    description: "Валюта, часовой пояс, БИН и служебные параметры.",
  },
  {
    href: "/dashboard/company/branding",
    title: "Брендинг и логотип",
    description: "Логотип на чеках и оформление счетов.",
  },
  {
    href: "/dashboard/company/invoice-settings",
    title: "Настройки счетов",
    description: "Префиксы, нумерация и налоги.",
  },
];

export default function SettingsHubPage(): ReactElement {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">Настройки</h1>
        <p className="max-w-2xl text-muted-foreground">Управление магазином, чеками и параметрами компании.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {settingsLinks.map((item) => (
          <Link key={item.href} href={item.href} className="block transition-opacity hover:opacity-90">
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="text-lg">{item.title}</CardTitle>
                <CardDescription>{item.description}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
