from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


# =====================================================
# AI Tone
# =====================================================

class AITone(str, Enum):

    PROFESSIONAL = "professional"

    FRIENDLY = "friendly"

    CASUAL = "casual"

    FORMAL = "formal"


# =====================================================
# AI Personality
# =====================================================

class AIPersonality(str, Enum):

    RECEPTIONIST = "receptionist"

    SALES = "sales"

    CUSTOMER_SUPPORT = "customer_support"

    ASSISTANT = "assistant"


# =====================================================
# AI Profile
# =====================================================

@dataclass(slots=True)
class AIProfile:
    """
    Tenant AI Profile.

    Defines how the AI behaves
    for a specific tenant.
    """

    profile_id: str

    tenant_id: str

    name: str

    personality: AIPersonality = (
        AIPersonality.RECEPTIONIST
    )

    tone: AITone = (
        AITone.PROFESSIONAL
    )

    language: str = "en"

    greeting: str = (
        "Hello! How can I help you today?"
    )

    farewell: str = (
        "Thank you for contacting us."
    )

    escalation_enabled: bool = True

    qualification_enabled: bool = True

    appointment_booking_enabled: bool = True

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def update(

        self,

        **kwargs,

    ):

        for key, value in kwargs.items():

            if hasattr(self, key):

                setattr(

                    self,

                    key,

                    value,

                )

        self.updated_at = datetime.now(UTC)