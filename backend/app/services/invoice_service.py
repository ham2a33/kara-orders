from __future__ import annotations

import io
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.db.models.company import Company
from app.db.models.order import Order


class InvoiceService:
    _RECEIPT_WIDTH = 72 * mm
    _FONT_REGULAR = "ReceiptRegular"
    _FONT_BOLD = "ReceiptBold"
    _fonts_registered = False

    def generate_pdf(self, company: Company, order: Order) -> bytes:
        self._ensure_fonts()
        buffer = io.BytesIO()
        side_margin = max((A4[0] - self._RECEIPT_WIDTH) / 2, 12 * mm)
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=side_margin,
            rightMargin=side_margin,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
            title=f"Receipt {order.invoice_number}",
            author=company.name,
        )

        styles = self._build_styles()
        elements: list[object] = []

        store_name = (company.name or "").strip() or "Магазин"
        elements.append(Paragraph(self._escape(store_name), styles["brand"]))
        elements.append(Spacer(1, 3 * mm))

        store_lines = self._store_profile_lines(company)
        for line in store_lines:
            elements.append(Paragraph(line, styles["meta"]))
        if store_lines:
            elements.append(Spacer(1, 3 * mm))

        elements.append(self._divider_table())
        elements.append(Spacer(1, 4 * mm))

        elements.append(Paragraph(f"Товарный чек №{order.invoice_number}", styles["title"]))
        elements.append(Spacer(1, 4 * mm))

        elements.append(Paragraph(f"Дата:<br/>{self._format_receipt_datetime(company, order.created_at)}", styles["meta"]))
        elements.append(Spacer(1, 4 * mm))

        if order.customer_name and order.customer_name.strip():
            elements.append(Paragraph(f"Покупатель:<br/>{self._escape(order.customer_name.strip())}", styles["meta"]))
            elements.append(Spacer(1, 4 * mm))

        elements.append(self._divider_table())
        elements.append(Spacer(1, 4 * mm))
        for item in order.items:
            elements.extend(self._build_item_block(item, company.currency, styles))
            elements.append(Spacer(1, 3 * mm))

        elements.append(Spacer(1, 2 * mm))
        elements.append(self._divider_table())
        elements.append(Spacer(1, 3 * mm))
        elements.extend(self._build_totals(company, order, styles))
        elements.append(Spacer(1, 6 * mm))
        elements.append(self._divider_table())
        elements.append(Spacer(1, 4 * mm))
        closing = (company.footer_text or "").strip() or "Спасибо за покупку!"
        elements.append(Paragraph(self._escape(closing), styles["footer"]))
        signature = (company.receipt_signature or "").strip()
        if signature:
            elements.append(Spacer(1, 3 * mm))
            elements.append(Paragraph(self._escape(signature).replace("\n", "<br/>"), styles["footer"]))

        document.build(elements)
        return buffer.getvalue()

    def _build_styles(self) -> dict[str, ParagraphStyle]:
        regular = self._FONT_REGULAR
        bold = self._FONT_BOLD
        return {
            "brand": ParagraphStyle(
                "ReceiptBrand",
                fontName=bold,
                fontSize=11,
                leading=14,
                alignment=TA_CENTER,
                spaceAfter=0,
            ),
            "title": ParagraphStyle(
                "ReceiptTitle",
                fontName=bold,
                fontSize=10,
                leading=13,
                alignment=TA_CENTER,
                spaceAfter=0,
            ),
            "meta": ParagraphStyle(
                "ReceiptMeta",
                fontName=regular,
                fontSize=8.5,
                leading=12,
                alignment=TA_LEFT,
                spaceAfter=2,
            ),
            "itemName": ParagraphStyle(
                "ReceiptItemName",
                fontName=regular,
                fontSize=8.5,
                leading=11,
                alignment=TA_LEFT,
                spaceAfter=0,
            ),
            "itemLine": ParagraphStyle(
                "ReceiptItemLine",
                fontName=regular,
                fontSize=8.5,
                leading=11,
                alignment=TA_LEFT,
                spaceAfter=0,
            ),
            "itemLineRight": ParagraphStyle(
                "ReceiptItemLineRight",
                fontName=regular,
                fontSize=8.5,
                leading=11,
                alignment=TA_RIGHT,
                spaceAfter=0,
            ),
            "totalLabel": ParagraphStyle(
                "ReceiptTotalLabel",
                fontName=regular,
                fontSize=9,
                leading=12,
                alignment=TA_LEFT,
            ),
            "totalValue": ParagraphStyle(
                "ReceiptTotalValue",
                fontName=regular,
                fontSize=9,
                leading=12,
                alignment=TA_RIGHT,
            ),
            "grandTotalLabel": ParagraphStyle(
                "ReceiptGrandLabel",
                fontName=bold,
                fontSize=10,
                leading=13,
                alignment=TA_LEFT,
            ),
            "grandTotalValue": ParagraphStyle(
                "ReceiptGrandValue",
                fontName=bold,
                fontSize=10,
                leading=13,
                alignment=TA_RIGHT,
            ),
            "footer": ParagraphStyle(
                "ReceiptFooter",
                fontName=regular,
                fontSize=9,
                leading=12,
                alignment=TA_CENTER,
                spaceBefore=4,
            ),
        }

    def _store_profile_lines(self, company: Company) -> list[str]:
        rows: list[tuple[str, str | None]] = [
            ("БИН", company.bin_tax_id),
            ("Адрес", company.address),
            ("Телефон", company.phone),
            ("Instagram", self._format_instagram(company.instagram)),
            ("Эл. почта", company.email),
            ("Сайт", company.website),
            ("Руководитель", company.director_name),
        ]
        lines: list[str] = []
        for label, value in rows:
            if value is None:
                continue
            cleaned = str(value).strip()
            if not cleaned:
                continue
            lines.append(f"{label}:<br/>{self._escape(cleaned)}")
        return lines

    def _format_instagram(self, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if cleaned.startswith("@"):
            return cleaned
        if "instagram.com" in cleaned.lower():
            return cleaned
        return f"@{cleaned.lstrip('@')}"

    def _build_item_block(self, item, currency: str, styles: dict[str, ParagraphStyle]) -> list[object]:
        qty_price = f"{self._format_decimal(item.quantity)} × {self._format_money(item.unit_price, currency)}"
        line_total = self._format_money(item.line_total, currency)
        name_row = Table([[Paragraph(self._escape(item.product_name), styles["itemName"])]], colWidths=[self._RECEIPT_WIDTH])
        name_row.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
        detail_row = Table(
            [
                [
                    Paragraph(qty_price, styles["itemLine"]),
                    Paragraph(line_total, styles["itemLineRight"]),
                ]
            ],
            colWidths=[self._RECEIPT_WIDTH * 0.62, self._RECEIPT_WIDTH * 0.38],
        )
        detail_row.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return [name_row, Spacer(1, 1.5 * mm), detail_row]

    def _build_totals(self, company: Company, order: Order, styles: dict[str, ParagraphStyle]) -> list[object]:
        currency = company.currency
        vat_label = f"НДС ({self._format_tax_rate(company.tax_percentage)}%)"
        rows: list[tuple[str, str, ParagraphStyle, ParagraphStyle]] = [
            ("Подытог", self._format_money(order.subtotal, currency), styles["totalLabel"], styles["totalValue"]),
        ]
        if order.discount_total and order.discount_total > 0:
            rows.append(
                (
                    "Скидка",
                    self._format_money(order.discount_total, currency),
                    styles["totalLabel"],
                    styles["totalValue"],
                )
            )
        rows.append((vat_label, self._format_money(order.tax_total, currency), styles["totalLabel"], styles["totalValue"]))
        rows.append(("ИТОГО", self._format_money(order.total, currency), styles["grandTotalLabel"], styles["grandTotalValue"]))

        table_data = [[Paragraph(label, label_style), Paragraph(value, value_style)] for label, value, label_style, value_style in rows]
        table = Table(table_data, colWidths=[self._RECEIPT_WIDTH * 0.55, self._RECEIPT_WIDTH * 0.45])
        table.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("LINEABOVE", (0, -1), (-1, -1), 0.6, colors.black),
                ]
            )
        )
        return [table]

    def _divider_table(self) -> Table:
        table = Table([["-" * 42]], colWidths=[self._RECEIPT_WIDTH])
        table.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("FONTNAME", (0, 0), (-1, -1), self._FONT_REGULAR),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#444444")),
                ]
            )
        )
        return table

    def _format_receipt_datetime(self, company: Company, created_at: datetime) -> str:
        tz_name = (company.timezone or "Asia/Almaty").strip() or "Asia/Almaty"
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("Asia/Almaty")
        moment = created_at
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=ZoneInfo("UTC"))
        local = moment.astimezone(tz)
        return local.strftime("%d.%m.%Y %H:%M")

    def _format_tax_rate(self, value: Decimal) -> str:
        normalized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if normalized == normalized.to_integral():
            return str(int(normalized))
        return f"{normalized:f}".rstrip("0").rstrip(".")

    def _format_decimal(self, value: Decimal) -> str:
        normalized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        text = f"{normalized:f}"
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text

    def _format_money(self, value: Decimal, currency: str) -> str:
        amount = self._format_decimal(value)
        if currency.upper() == "KZT":
            return f"{amount} ₸"
        return f"{amount} {currency.upper()}"

    def _escape(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _ensure_fonts(self) -> None:
        if self._fonts_registered:
            return
        assets = Path(__file__).resolve().parent.parent / "assets" / "fonts"
        regular_candidates = [
            assets / "DejaVuSans.ttf",
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        ]
        bold_candidates = [
            assets / "DejaVuSans-Bold.ttf",
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            *regular_candidates,
        ]
        regular_path = next((path for path in regular_candidates if path.is_file()), None)
        bold_path = next((path for path in bold_candidates if path.is_file()), regular_path)
        if regular_path is None:
            raise RuntimeError("Receipt font not found. Install DejaVuSans or add backend/app/assets/fonts/DejaVuSans.ttf")
        pdfmetrics.registerFont(TTFont(self._FONT_REGULAR, str(regular_path)))
        pdfmetrics.registerFont(TTFont(self._FONT_BOLD, str(bold_path or regular_path)))
        self._fonts_registered = True
