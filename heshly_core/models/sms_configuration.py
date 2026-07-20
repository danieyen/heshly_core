from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class SMSProvider(str, Enum):
    AFRICASTALKING = "africastalking"
    TWILIO = "twilio"
    VONAGE = "vonage"
    AWS_SNS = "aws_sns"
    INFOBIP = "infobip"
    MESSAGEBIRD = "messagebird"


@dataclass(slots=True)
class SMSConfiguration:
    """
    Tenant SMS Configuration.
    """

    configuration_id: str

    tenant_id: str

    provider: SMSProvider = SMSProvider.AFRICASTALKING

    sender_id: str = ""

    api_key: str = ""

    api_secret: str = ""

    username: str = ""

    enabled: bool = False

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