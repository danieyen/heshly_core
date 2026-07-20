from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class EmailConfiguration:
    """
    Tenant Email Configuration.
    """

    configuration_id: str

    tenant_id: str

    provider: str = "smtp"

    sender_name: str = ""

    sender_email: str = ""

    smtp_host: str = ""

    smtp_port: int = 587

    username: str = ""

    password: str = ""

    use_tls: bool = True

    enabled: bool = False

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