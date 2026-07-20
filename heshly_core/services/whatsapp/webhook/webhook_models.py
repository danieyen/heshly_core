from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class WebhookEventType(str, Enum):
    """
    Supported WhatsApp webhook events.
    """

    MESSAGE = "message"

    STATUS = "status"

    MEDIA = "media"

    UNKNOWN = "unknown"


@dataclass(slots=True)
class WebhookVerificationRequest:
    """
    Meta webhook verification challenge.
    """

    mode: str

    verify_token: str

    challenge: str


@dataclass(slots=True)
class WebhookVerificationResult:
    """
    Result of webhook verification.
    """

    success: bool

    challenge: str | None = None

    message: str = ""


@dataclass(slots=True)
class WebhookEvent:
    """
    Generic webhook event received
    from Meta.
    """

    event_type: WebhookEventType

    payload: dict[str, Any]

    received_at: datetime = field(
        default_factory=datetime.utcnow
    )


@dataclass(slots=True)
class IncomingMessageEvent:
    """
    Incoming customer message.
    """

    message_id: str

    phone_number: str

    customer_name: str | None

    message_type: str

    text: str | None = None

    timestamp: str | None = None


@dataclass(slots=True)
class MessageStatusEvent:
    """
    Delivery/read status update.
    """

    message_id: str

    recipient_id: str

    status: str

    timestamp: str | None = None


@dataclass(slots=True)
class MediaEvent:
    """
    Media received from WhatsApp.
    """

    message_id: str

    media_id: str

    media_type: str

    mime_type: str | None = None

    sha256: str | None = None

    caption: str | None = None


@dataclass(slots=True)
class WebhookProcessingResult:
    """
    Result returned after a webhook
    has been processed.
    """

    success: bool

    event_type: WebhookEventType

    message: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )