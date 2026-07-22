import type { Metadata } from "next";
import type { ReactElement, ReactNode } from "react";

import Providers from "@/app/providers";

import "./globals.css";

export const metadata: Metadata = {
  title: "Kara Orders — управление заказами",
  description: "Премиальная SaaS-платформа для заказов, товаров, аналитики и счетов.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>): ReactElement {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
