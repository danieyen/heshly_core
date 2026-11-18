from __future__ import annotations

import uuid

from heshly_core.models.crm import WhatsAppActivity
from heshly_core.models.whatsapp import (
    WhatsAppDirection,
    WhatsAppDeliveryStatus,
)
from heshly_core.repositories.whatsapp_activity_repository import (
    WhatsAppActivityRepository,
)


class WhatsAppMessageStatus:
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    RECEIVED = "received"
    FAILED = "failed"


class WhatsAppActivityLoggingError(Exception):
    pass


class WhatsAppActivityLogger:
    """
    Persistent WhatsApp activity logger.

    Persistence:
        WhatsAppActivityLogger
            -> WhatsAppActivityRepository
            -> Heshly WhatsApp Activity

    Tenant isolation is handled by the repository through
    TenantContext.
    """

    def __init__(
        self,
        repository: WhatsAppActivityRepository | None = None,
        tenant_id: str | None = None,
    ):
        self.repository = (
            repository
            or WhatsAppActivityRepository(
                tenant_id=tenant_id
            )
        )

        if tenant_id:
            self.repository.set_tenant(
                tenant_id
            )

    def set_tenant(self, tenant_id: str) -> None:
        if not tenant_id:
            raise ValueError("tenant_id is required.")

        self.repository.set_tenant(tenant_id)

    # =====================================================
    # Log Message
    # =====================================================

    def log_message(
        self,
        business_id: str,
        related_type: str,
        related_id: str,
        direction: WhatsAppDirection | str,
        phone_number: str,
        message: str,
        status: WhatsAppMessageStatus | str,
        logged_by: str | None = None,
        message_id: str | None = None,
    ) -> WhatsAppActivity:

        if not business_id:
            raise WhatsAppActivityLoggingError(
                "Business ID is required."
            )

        if not related_id:
            raise WhatsAppActivityLoggingError(
                "Related ID is required."
            )

        if not phone_number or not phone_number.strip():
            raise WhatsAppActivityLoggingError(
                "Phone number is required."
            )

        if not message or not message.strip():
            raise WhatsAppActivityLoggingError(
                "Message is required."
            )

        if isinstance(direction, WhatsAppDirection):
            direction = direction.value

        if hasattr(status, "value"):
            status = status.value

        # Webhook delivery is retryable. Meta may deliver the same
        # inbound message more than once, so message_id + direction
        # must be idempotent within a tenant.
        if message_id:
            existing = self.repository.find_by_message_id(
                message_id
            )

            if existing is not None:
                return existing

        activity = WhatsAppActivity(
            activity_id=self._generate_activity_id(),
            business_id=business_id,
            related_type=related_type,
            related_id=related_id,
            message_id=(
                message_id
                or self._generate_message_id()
            ),
            direction=direction,
            phone_number=phone_number,
            message=message,
            status=status,
            logged_by=logged_by,
        )

        return self.repository.save(activity)

    # =====================================================
    # History
    # =====================================================

    def get_history(
        self,
        related_type: str,
        related_id: str,
    ) -> list[WhatsAppActivity]:

        return self.repository.find_by_related(
            related_type=related_type,
            related_id=related_id,
        )

    # =====================================================
    # Lookup
    # =====================================================

    def get(
        self,
        activity_id: str,
    ) -> WhatsAppActivity | None:

        return self.repository.get(activity_id)

    def get_by_message_id(
        self,
        message_id: str,
    ) -> WhatsAppActivity | None:

        return self.repository.find_by_message_id(
            message_id
        )

    def get_by_phone(
        self,
        phone_number: str,
    ) -> list[WhatsAppActivity]:

        return self.repository.find_by_phone(
            phone_number
        )

    # =====================================================
    # Analytics
    # =====================================================

    def count(self) -> int:

        return self.repository.count()

    def count_by_status(
        self,
        status: str,
    ) -> int:

        return self.repository.count_by_status(
            status
        )

    def count_by_direction(
        self,
        direction: str | WhatsAppDirection,
    ) -> int:

        if isinstance(direction, WhatsAppDirection):
            direction = direction.value

        return self.repository.count_by_direction(
            direction
        )

    def latest(
        self,
        limit: int = 10,
    ) -> list[WhatsAppActivity]:

        return self.repository.latest(limit)

    # =====================================================
    # IDs
    # =====================================================

    def _generate_activity_id(self) -> str:

        return (
            f"WAA-{uuid.uuid4().hex[:8].upper()}"
        )

    def _generate_message_id(self) -> str:

        return (
            f"MSG-{uuid.uuid4().hex[:10].upper()}"
        )
