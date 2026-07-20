from __future__ import annotations

import uuid

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class WhatsAppDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class WhatsAppMessageStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    RECEIVED = "received"
    FAILED = "failed"


@dataclass(slots=True)
class WhatsAppActivity:

    activity_id: str

    business_id: str

    related_type: str

    related_id: str

    message_id: str

    direction: WhatsAppDirection

    phone_number: str

    message: str

    status: WhatsAppMessageStatus

    logged_by: str | None = None

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )


class WhatsAppActivityLoggingError(Exception):
    pass


class WhatsAppActivityLogger:

    def __init__(self):

        self.activities: list[
            WhatsAppActivity
        ] = []


    def log_message(
        self,
        business_id: str,
        related_type: str,
        related_id: str,
        direction: WhatsAppDirection,
        phone_number: str,
        message: str,
        status: WhatsAppMessageStatus,
        logged_by: str | None = None,
    ) -> WhatsAppActivity:

        if not business_id:
            raise WhatsAppActivityLoggingError(
                "Business ID is required."
            )

        if not related_id:
            raise WhatsAppActivityLoggingError(
                "Related ID is required."
            )

        if not phone_number.strip():
            raise WhatsAppActivityLoggingError(
                "Phone number is required."
            )

        if not message.strip():
            raise WhatsAppActivityLoggingError(
                "Message is required."
            )

        activity = WhatsAppActivity(

            activity_id=self._generate_activity_id(),

            business_id=business_id,

            related_type=related_type,

            related_id=related_id,

            message_id=self._generate_message_id(),

            direction=direction,

            phone_number=phone_number,

            message=message,

            status=status,

            logged_by=logged_by,

        )

        self.activities.append(activity)

        return activity


    def get_history(
        self,
        related_type: str,
        related_id: str,
    ) -> list[WhatsAppActivity]:

        return [

            activity

            for activity in self.activities

            if (
                activity.related_type == related_type
                and
                activity.related_id == related_id
            )

        ]


    def _generate_activity_id(self):

        return (
            f"WAA-{uuid.uuid4().hex[:8].upper()}"
        )


    def _generate_message_id(self):

        return (
            f"MSG-{uuid.uuid4().hex[:10].upper()}"
        )