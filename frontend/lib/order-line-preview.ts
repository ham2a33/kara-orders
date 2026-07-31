/** Mirrors backend order line math in order_service._build_items (preview only). */

export type LinePreviewInput = {
  quantity: number;
  unitPrice: number;
  discountAmount: number;
  taxPercent: number;
};

export type LinePreview = {
  lineSubtotal: number;
  discountAmount: number;
  taxableBase: number;
  taxAmount: number;
  lineTotal: number;
};

function quantize(value: number): number {
  return Math.round(value * 100) / 100;
}

export function previewOrderLine(input: LinePreviewInput): LinePreview {
  const lineSubtotal = quantize(input.quantity * input.unitPrice);
  const discountAmount = quantize(Math.min(input.discountAmount, lineSubtotal));
  const taxableBase = quantize(lineSubtotal - discountAmount);
  const taxAmount = quantize((taxableBase * input.taxPercent) / 100);
  const lineTotal = quantize(taxableBase + taxAmount);
  return { lineSubtotal, discountAmount, taxableBase, taxAmount, lineTotal };
}

export type OrderTotalsPreview = {
  subtotal: number;
  discountTotal: number;
  taxTotal: number;
  total: number;
};

export function previewOrderTotals(lines: LinePreview[]): OrderTotalsPreview {
  const subtotal = quantize(lines.reduce((sum, line) => sum + line.lineSubtotal, 0));
  const discountTotal = quantize(lines.reduce((sum, line) => sum + line.discountAmount, 0));
  const taxTotal = quantize(lines.reduce((sum, line) => sum + line.taxAmount, 0));
  const total = quantize(subtotal - discountTotal + taxTotal);
  return { subtotal, discountTotal, taxTotal, total };
}
