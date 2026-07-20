from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class AIPersonalitySettings:
    """
    AI Personality Settings.

    Fine-grained behaviour controls
    for a tenant's AI.
    """

    tenant_id: str

    friendliness: int = 5

    formality: int = 5

    empathy: int = 5

    enthusiasm: int = 5

    conciseness: int = 5

    proactiveness: int = 5

    emoji_usage: bool = False

    allow_small_talk: bool = False

    upsell_services: bool = True

    max_response_sentences: int = 5

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def update(self, **kwargs):

        for key, value in kwargs.items():

            if hasattr(self, key):

                setattr(self, key, value)

        self.updated_at = datetime.now(UTC)