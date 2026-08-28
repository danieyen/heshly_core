from dataclasses import dataclass, field
from datetime import datetime, UTC
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

    payload: Any

    received_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


@dataclass(slots=True)
class IncomingMessageEvent:
    """
    Incoming customer message.

    tenant_id identifies the Heshly tenant that owns
    the WhatsApp number receiving the message.
    Must be resolved via phone_number_id -> tenant mapping,
    never defaulted to "default" in production.
    """

    message_id: str

    phone_number: str

    customer_name: str | None

    message_type: str

    text: str | None = None

    timestamp: str | None = None

    phone_number_id: str | None = None

    tenant_id: str = field(default="")

    def __post_init__(self):
        if not self.message_id:
            raise ValueError("message_id is required")
        if not self.phone_number:
            raise ValueError("phone_number is required")
        if not self.tenant_id:
            raise ValueError("tenant_id is required - tenant resolution failed")


@dataclass(slots=True)
class MessageStatusEvent:
    """
    Delivery/read status update.
    """

    message_id: str

    recipient_id: str

    status: str

    timestamp: str | None = None

    def __post_init__(self):
        if not self.message_id:
            raise ValueError("message_id is required")


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

    def __post_init__(self):
        if not self.message_id:
            raise ValueError("message_id is required")
        if not self.media_id:
            raise ValueError("media_id is required")


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
