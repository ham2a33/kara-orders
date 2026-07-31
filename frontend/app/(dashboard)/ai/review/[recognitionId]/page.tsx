"use client";

import { useEffect, type ReactElement } from "react";
import { useParams, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

export default function AiReviewRedirectPage(): ReactElement {
  const params = useParams<{ recognitionId: string }>();
  const router = useRouter();

  useEffect(() => {
    if (params.recognitionId) {
      router.replace(`/orders/new?recognitionId=${params.recognitionId}`);
    }
  }, [params.recognitionId, router]);

  return (
    <div className="flex min-h-[40vh] items-center justify-center text-sm text-muted-foreground">
      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      Открываем редактор заказа…
    </div>
  );
}
