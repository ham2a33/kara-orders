from __future__ import annotations

from app.schemas.ai import AIExtractionPayload


class PromptManager:
    def build_instruction(self) -> str:
        return (
            "You extract order line items from customer notes, photos, voice transcripts, and supplier PDFs. "
            "Return JSON only. Never include markdown, explanations, or prices. "
            "If quantities are unclear, make the safest structured extraction and lower confidence."
        )

    def build_context(self, *, source_type: str) -> str:
        return (
            f"Source type: {source_type}.\n"
            "Extract product names and quantities exactly as described.\n"
            "Do not invent products.\n"
            "Do not calculate prices.\n"
            "Use units when visible; otherwise set unit to null.\n"
            "Confidence must be between 0 and 1."
        )

    def schema(self) -> dict[str, object]:
        return AIExtractionPayload.model_json_schema()
