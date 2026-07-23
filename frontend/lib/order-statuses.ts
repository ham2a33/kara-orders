import type { OrderStatus } from "@/types/orders";

export const ORDER_STATUS_OPTIONS: Array<{ value: OrderStatus; label: string }> = [
  { value: "new", label: "Новый" },
  { value: "confirmed", label: "Подтвержден" },
  { value: "deleted", label: "Удален" },
];

export function orderStatusLabel(status: OrderStatus | string): string {
  switch (status) {
    case "new":
      return "Новый";
    case "confirmed":
      return "Подтвержден";
    case "deleted":
      return "Удален";
    default:
      return status;
  }
}

export function orderStatusBadgeVariant(status: OrderStatus | string): "default" | "outline" | "success" | "warning" | "danger" {
  if (status === "confirmed") {
    return "success";
  }
  if (status === "deleted") {
    return "danger";
  }
  return "outline";
}
