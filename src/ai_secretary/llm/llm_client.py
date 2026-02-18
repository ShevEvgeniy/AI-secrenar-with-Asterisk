"""LLM client abstraction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMClient:
    """Client for LLM completion calls."""

    model: str

    def complete(self, prompt: str) -> str:
        """Return a completion for the prompt (placeholder)."""
        _ = prompt
        return ""
