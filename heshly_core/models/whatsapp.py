from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class WhatsAppMessageType(str, Enum):
    """
    Supported WhatsApp message types.
    """

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACT = "contact"
    INTERACTIVE = "interactive"
    TEMPLATE = "template"


class WhatsAppDirection(str, Enum):
    """
    Message direction.
    """

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class WhatsAppDeliveryStatus(str, Enum):
    """
    Delivery state.
    """

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass(slots=True)
class WhatsAppContact:
    """
    WhatsApp customer.
    """

    phone_number: str

    display_name: str | None = None

    whatsapp_id: str | None = None


@dataclass(slots=True)
class WhatsAppMedia:
    """
    Media attached to a message.
    """

    media_id: str

    media_type: WhatsAppMessageType

    mime_type: str

    filename: str | None = None

    caption: str | None = None


@dataclass(slots=True)
class WhatsAppMessage:
    """
    WhatsApp message.
    """

    message_id: str

    conversation_id: str

    contact: WhatsAppContact

    direction: WhatsAppDirection

    message_type: WhatsAppMessageType

    text: str | None = None

    media: WhatsAppMedia | None = None

    status: WhatsAppDeliveryStatus = (
        WhatsAppDeliveryStatus.PENDING
    )

    timestamp: datetime = field(
        default_factory=datetime.utcnow
    )

    metadata: dict[str, str] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class WhatsAppWebhookEvent:
    """
    Incoming webhook payload.
    """

    event_id: str

    message: WhatsAppMessage

    received_at: datetime = field(
        default_factory=datetime.utcnow
    )


@dataclass(slots=True)
class WhatsAppConfiguration:
    """
    WhatsApp Cloud API configuration.

    Mirrors the persistent Heshly WhatsApp Configuration
    DocType and is the runtime configuration contract used
    by the WhatsApp services.
    """

    configuration_id: str
    tenant_id: str
    business_id: str
    business_account_id: str
    phone_number_id: str

    access_token: str
    verify_token: str
    app_secret: str

    display_phone_number: str = ""
    webhook_url: str = ""
    language: str = "en"
    api_version: str = "v23.0"
    webhook_enabled: bool = True
    business_name: str = ""


@dataclass(slots=True)
class WhatsAppConfigurationValidation:
    """
    Configuration validation result.
    """

    valid: bool

    errors: list[str] = field(
        default_factory=list
    )