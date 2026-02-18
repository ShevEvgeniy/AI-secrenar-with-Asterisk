"""Summary agent for producing call summaries."""

from __future__ import annotations

from dataclasses import dataclass
from .llm_client import LLMClient
from ..core.models import Summary


@dataclass
class SummaryAgent:
    """Produces a summary from dialogue text."""

    client: LLMClient

    def summarize(self, dialogue_text: str) -> Summary:
        """Summarize dialogue text (placeholder)."""
        _ = dialogue_text
        return Summary(text="")
