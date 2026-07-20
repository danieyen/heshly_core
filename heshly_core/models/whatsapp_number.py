from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class WhatsAppNumber:
    """
    WhatsApp Number.

    Represents a WhatsApp Business
    phone number owned by a tenant.
    """

    number_id: str

    tenant_id: str

    phone_number: str

    phone_number_id: str

    display_name: str

    verified: bool = False

    active: bool = True

    primary: bool = False

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def verify(self):

        self.verified = True

        self.updated_at = datetime.now(UTC)

    def activate(self):

        self.active = True

        self.updated_at = datetime.now(UTC)

    def deactivate(self):

        self.active = False

        self.updated_at = datetime.now(UTC)