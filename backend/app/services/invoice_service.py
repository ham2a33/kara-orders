from __future__ import annotations

import io
from decimal import Decimal, ROUND_HALF_UP
from urllib.request import urlopen

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.db.models.company import Company
from app.db.models.order import Order


class InvoiceService:
    def generate_pdf(self, company: Company, order: Order) -> bytes:
        buffer = io.BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=f"Invoice {order.invoice_number}",
            author=company.name,
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="InvoiceTitle", parent=styles["Title"], fontSize=20, leading=24, spaceAfter=8))
        styles.add(ParagraphStyle(name="InvoiceMeta", parent=styles["BodyText"], fontSize=9, leading=12))
        styles.add(ParagraphStyle(name="InvoiceSection", parent=styles["Heading2"], fontSize=12, leading=14))

        elements: list[object] = []
        logo = self._load_logo(company.invoice_logo_url or company.logo_url)
        if logo is not None:
            elements.append(logo)
            elements.append(Spacer(1, 6))

        elements.append(Paragraph("Invoice", styles["InvoiceTitle"]))
        elements.append(Paragraph(f"Invoice No: {order.invoice_number}", styles["InvoiceMeta"]))
        elements.append(Paragraph(f"Date: {order.created_at:%Y-%m-%d}", styles["InvoiceMeta"]))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph(company.name, styles["InvoiceSection"]))
        company_lines = [
            company.address,
            company.phone,
            company.email,
            company.website,
            f"BIN / Tax ID: {company.bin_tax_id}" if company.bin_tax_id else None,
        ]
        for line in company_lines:
            if line:
                elements.append(Paragraph(str(line), styles["InvoiceMeta"]))

        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Customer information", styles["InvoiceSection"]))
        customer_lines = [
            order.customer_name,
            order.customer_phone,
            order.customer_address,
            order.notes,
        ]
        for line in customer_lines:
            if line:
                elements.append(Paragraph(str(line), styles["InvoiceMeta"]))

        elements.append(Spacer(1, 12))
        table_data = [
            ["Product", "Qty", "Unit price", "Discount", "Tax", "Total"],
        ]
        for item in order.items:
            table_data.append(
                [
                    item.product_name,
                    self._format_decimal(item.quantity),
                    self._format_money(item.unit_price),
                    self._format_money(item.discount_amount),
                    self._format_money(item.tax_amount),
                    self._format_money(item.line_total),
                ]
            )

        table = Table(table_data, repeatRows=1, colWidths=[62 * mm, 18 * mm, 24 * mm, 24 * mm, 20 * mm, 25 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LEADING", (0, 0), (-1, -1), 11),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d1d5db")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(table)
        elements.append(Spacer(1, 12))

        totals_data = [
            ["Subtotal", self._format_money(order.subtotal)],
            ["Discount", self._format_money(order.discount_total)],
            ["Tax", self._format_money(order.tax_total)],
            ["Grand total", self._format_money(order.total)],
        ]
        totals = Table(totals_data, colWidths=[40 * mm, 30 * mm], hAlign="RIGHT")
        totals.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.HexColor("#111827")),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        elements.append(totals)

        if company.payment_information:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("Payment information", styles["InvoiceSection"]))
            elements.append(Paragraph(company.payment_information, styles["InvoiceMeta"]))

        if company.footer_text:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(company.footer_text, styles["InvoiceMeta"]))

        document.build(elements)
        return buffer.getvalue()

    def _load_logo(self, url: str | None) -> Image | None:
        if not url:
            return None
        try:
            with urlopen(url, timeout=10) as response:
                data = response.read()
        except Exception:
            return None
        return Image(io.BytesIO(data), width=45 * mm, height=20 * mm)

    def _format_decimal(self, value: Decimal) -> str:
        return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):f}"

    def _format_money(self, value: Decimal) -> str:
        return self._format_decimal(value)
