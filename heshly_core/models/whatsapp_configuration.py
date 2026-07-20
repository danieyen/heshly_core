from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class WhatsAppConfiguration:
    """
    Tenant WhatsApp Configuration.
    """

    configuration_id: str

    tenant_id: str

    business_account_id: str = ""

    phone_number_id: str = ""

    display_phone_number: str = ""

    verify_token: str = ""

    access_token: str = ""

    webhook_url: str = ""

    language: str = "en"

    webhook_enabled: bool = False

    sandbox_mode: bool = True

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