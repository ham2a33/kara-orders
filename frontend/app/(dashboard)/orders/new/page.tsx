import { Suspense, type ReactElement } from "react";
import { Loader2 } from "lucide-react";

import { NewOrderPageClient } from "./new-order-page-client";

function NewOrderPageFallback(): ReactElement {
  return (
    <div className="flex min-h-[40vh] items-center justify-center text-sm text-muted-foreground">
      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      Загружаем форму заказа…
    </div>
  );
}

export default function NewOrderPage(): ReactElement {
  return (
    <Suspense fallback={<NewOrderPageFallback />}>
      <NewOrderPageClient />
    </Suspense>
  );
}
