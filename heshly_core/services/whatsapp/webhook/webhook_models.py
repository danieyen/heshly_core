from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any


def _parse_json_if_string(value: Any) -> Any:
    if isinstance(value, str):
        import json
        value = value.strip()
        if value.startswith("{") and value.endswith("}"):
            try:
                return json.loads(value)
            except Exception:
                return value
    return value


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

    @classmethod
    def from_dict(cls, data: Any) -> "IncomingMessageEvent":
        data = _parse_json_if_string(data)
        if not isinstance(data, dict):
            raise ValueError("IncomingMessageEvent data must be dict")
        # Handle n8n $json.body nesting
        if "body" in data and isinstance(data["body"], dict):
            # Check if body contains the actual event
            body = data["body"]
            if "message_id" in body or "phone_number" in body:
                data = body
        if "json" in data and isinstance(data["json"], dict):
            inner = data["json"]
            if "message_id" in inner:
                data = inner
        return cls(
            message_id=str(data.get("message_id") or data.get("messageId") or data.get("id") or ""),
            phone_number=str(data.get("phone_number") or data.get("phoneNumber") or data.get("from") or ""),
            customer_name=data.get("customer_name") or data.get("customerName") or data.get("profile", {}).get("name") if isinstance(data.get("profile"), dict) else data.get("customer_name"),
            message_type=str(data.get("message_type") or data.get("messageType") or data.get("type") or "text"),
            text=data.get("text") or data.get("body"),
            timestamp=str(data.get("timestamp") or "") if data.get("timestamp") else None,
            phone_number_id=str(data.get("phone_number_id") or data.get("phoneNumberId") or "") if data.get("phone_number_id") or data.get("phoneNumberId") else None,
            tenant_id=str(data.get("tenant_id") or data.get("tenantId") or "").strip(),
        )

    @classmethod
    def parse_meta_payload(cls, payload: Any, tenant_resolver=None) -> "IncomingMessageEvent":
        """
        Parse raw Meta webhook payload: {entry: [{changes: [{value: {messages: [...], metadata: {phone_number_id}}}]}]}
        Resolves tenant_id via phone_number_id if resolver provided.
        """
        payload = _parse_json_if_string(payload)
        if not isinstance(payload, dict):
            raise ValueError("Meta payload must be dict")

        # Handle n8n wrapping
        if "body" in payload and isinstance(payload["body"], dict):
            payload = payload["body"]
        if "json" in payload and isinstance(payload["json"], dict):
            payload = payload["json"]

        # Direct IncomingMessageEvent shape - use from_dict
        if "message_id" in payload and "phone_number" in payload:
            return cls.from_dict(payload)

        # Meta webhook shape
        try:
            entry = (payload.get("entry") or [{}])[0]
            changes = (entry.get("changes") or [{}])[0]
            value = changes.get("value") or {}
            messages = value.get("messages") or []
            contacts = value.get("contacts") or []
            metadata = value.get("metadata") or {}

            if not messages:
                raise ValueError("No messages in Meta payload")

            msg = messages[0]
            contact = contacts[0] if contacts else {}

            message_id = str(msg.get("id") or "")
            phone_number = str(msg.get("from") or "")
            phone_number_id = str(metadata.get("phone_number_id") or value.get("phone_number_id") or "")
            customer_name = contact.get("profile", {}).get("name") if isinstance(contact.get("profile"), dict) else contact.get("wa_id")
            message_type = str(msg.get("type") or "text")
            text = None
            if message_type == "text" and isinstance(msg.get("text"), dict):
                text = msg["text"].get("body")
            elif isinstance(msg.get("text"), str):
                text = msg["text"]

            timestamp = str(msg.get("timestamp") or "")

            tenant_id = ""
            if tenant_resolver and phone_number_id:
                try:
                    tenant_id = tenant_resolver(phone_number_id) or ""
                except Exception:
                    tenant_id = ""
            # Also check if payload already has tenant_id
            if not tenant_id:
                tenant_id = str(payload.get("tenant_id") or payload.get("tenantId") or "").strip()

            return cls(
                message_id=message_id,
                phone_number=phone_number,
                customer_name=customer_name,
                message_type=message_type,
                text=text,
                timestamp=timestamp,
                phone_number_id=phone_number_id,
                tenant_id=tenant_id,
            )
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to parse Meta payload: {e}")

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "phone_number": self.phone_number,
            "customer_name": self.customer_name,
            "message_type": self.message_type,
            "text": self.text,
            "timestamp": self.timestamp,
            "phone_number_id": self.phone_number_id,
            "tenant_id": self.tenant_id,
        }


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

    def to_dict(self) -> dict:
        return {
            "success": bool(self.success),
            "event_type": self.event_type.value if isinstance(self.event_type, Enum) else str(self.event_type),
            "message": self.message,
            "metadata": self.metadata,
        }
