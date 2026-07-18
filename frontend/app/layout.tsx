import type { Metadata } from "next";
import type { ReactElement, ReactNode } from "react";

import Providers from "@/app/providers";

import "./globals.css";

export const metadata: Metadata = {
  title: "Kara Orders",
  description: "AI-assisted order and invoice foundation for small and medium businesses.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>): ReactElement {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
