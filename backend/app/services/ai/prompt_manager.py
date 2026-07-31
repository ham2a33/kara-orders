from __future__ import annotations


class PromptManager:
    def build_instruction(self) -> str:
        return (
            "You extract handwritten or printed order lines from photos and PDFs. "
            "Each physical line in the source is exactly one product line item. "
            "Return JSON only. Never include markdown, explanations, or prices. "
            "For each line determine: product_name (name without size), size, quantity, unit. "
            "Size is never quantity. Quantity is always the number immediately before the unit at the end of the line. "
            "If unit is missing, use шт."
        )

    def build_context(self, *, source_type: str) -> str:
        return (
            f"Source type: {source_type}.\n"
            "Rules:\n"
            "- ONE LINE = ONE ITEM.\n"
            "- Parse from the end: unit, then quantity, then size, then product_name.\n"
            "- Supported units: шт, м, кг, л, м², м³. Default unit: шт.\n"
            "- Examples:\n"
            '  "Труба 20 20 шт" -> product_name="Труба", size="20", quantity=20, unit="шт"\n'
            '  "Арматура 12 30 м" -> product_name="Арматура", size="12", quantity=30, unit="м"\n'
            '  "Кабель ВВГ 3x2.5 100 м" -> product_name="Кабель ВВГ", size="3x2.5", quantity=100, unit="м"\n'
            "- Put the original line text in source_line.\n"
            "- Confidence between 0 and 1."
        )

    def schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "items": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "product_name": {"type": "string", "minLength": 1, "maxLength": 255},
                            "size": {
                                "anyOf": [
                                    {"type": "string", "maxLength": 64},
                                    {"type": "null"},
                                ]
                            },
                            "quantity": {"type": "number", "exclusiveMinimum": 0},
                            "unit": {"type": "string", "maxLength": 32},
                            "source_line": {
                                "anyOf": [
                                    {"type": "string", "maxLength": 500},
                                    {"type": "null"},
                                ]
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                        "required": ["product_name", "size", "quantity", "unit", "source_line", "confidence"],
                    },
                }
            },
            "required": ["items"],
        }
