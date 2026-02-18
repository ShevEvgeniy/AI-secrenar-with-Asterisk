"""Response agent for producing final responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .llm_client import LLMClient
from ..core.models import Response


@dataclass
class ResponseAgent:
    """Produces a response using summary and context."""

    client: LLMClient

    def respond(self, summary_text: str, selected_chunks: Sequence[str]) -> Response:
        """Generate response text (placeholder)."""
        _ = (summary_text, selected_chunks)
        return Response(text="")
