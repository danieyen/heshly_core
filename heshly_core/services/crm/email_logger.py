from __future__ import annotations

import uuid

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EmailDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class EmailStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    OPENED = "opened"


@dataclass(slots=True)
class EmailLog:

    email_id: str

    business_id: str

    related_type: str

    related_id: str

    direction: EmailDirection

    sender: str

    recipient: str

    subject: str

    body: str

    status: EmailStatus = EmailStatus.DRAFT

    logged_by: str | None = None

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )


class EmailLoggingError(Exception):
    pass


class EmailLogger:

    def __init__(self):

        self.emails: list[EmailLog] = []


    def log_email(
        self,
        business_id: str,
        related_type: str,
        related_id: str,
        direction: EmailDirection,
        sender: str,
        recipient: str,
        subject: str,
        body: str,
        status: EmailStatus = EmailStatus.DRAFT,
        logged_by: str | None = None,
    ) -> EmailLog:

        if not business_id:
            raise EmailLoggingError(
                "Business ID is required."
            )

        if not related_id:
            raise EmailLoggingError(
                "Related ID is required."
            )

        if not sender.strip():
            raise EmailLoggingError(
                "Sender is required."
            )

        if not recipient.strip():
            raise EmailLoggingError(
                "Recipient is required."
            )

        if not subject.strip():
            raise EmailLoggingError(
                "Subject is required."
            )

        email = EmailLog(

            email_id=self._generate_id(),

            business_id=business_id,

            related_type=related_type,

            related_id=related_id,

            direction=direction,

            sender=sender,

            recipient=recipient,

            subject=subject,

            body=body,

            status=status,

            logged_by=logged_by,

        )

        self.emails.append(email)

        return email


    def get_emails(
        self,
        related_type: str,
        related_id: str,
    ) -> list[EmailLog]:

        return [

            email

            for email in self.emails

            if (
                email.related_type == related_type
                and
                email.related_id == related_id
            )

        ]


    def _generate_id(self):

        return (
            f"EMAIL-{uuid.uuid4().hex[:8].upper()}"
        )