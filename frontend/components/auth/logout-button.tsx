"use client";

import { useRouter } from "next/navigation";
import type { ReactElement } from "react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { clearStoredAuth } from "@/lib/auth";

export function LogoutButton(): ReactElement {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleLogout = async (): Promise<void> => {
    setIsLoading(true);
    try {
      await apiClient("/auth/logout", { method: "POST" });
    } finally {
      clearStoredAuth();
      setIsLoading(false);
      router.replace("/login");
    }
  };

  return (
    <Button variant="outline" className="w-full" onClick={handleLogout} disabled={isLoading}>
      {isLoading ? "Signing out..." : "Sign out"}
    </Button>
  );
}
