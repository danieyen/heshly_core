from __future__ import annotations

import frappe

import uuid

from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
    WhatsAppContact,
    WhatsAppDirection,
    WhatsAppMessage,
    WhatsAppMessageType,
)

from heshly_core.repositories.whatsapp_configuration_repository import (
    WhatsAppConfigurationRepository,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)

from heshly_core.services.whatsapp.conversation_orchestrator import (
    WhatsAppConversationOrchestrator,
)

from heshly_core.services.whatsapp.outgoing_message_sender import (
    WhatsAppOutgoingMessageSender,
)

from heshly_core.services.crm.whatsapp_activity_logger import (
    WhatsAppActivityLogger,
)

from heshly_core.services.whatsapp.webhook.webhook_models import (
    IncomingMessageEvent,
)


class WhatsAppConversationFlow:
    """
    Complete WhatsApp conversation flow.

    Incoming message
        -> AI receptionist
        -> conversation persistence
        -> outgoing WhatsApp reply
    """

    def __init__(self) -> None:
        self._orchestrator = (
            WhatsAppConversationOrchestrator()
        )

        self._sender = (
            WhatsAppOutgoingMessageSender()
        )

        self._activity_logger = (
            WhatsAppActivityLogger()
        )

        self._configurations = (
            WhatsAppConfigurationRepository()
        )

        self._tenant_context = TenantContext()

    @staticmethod
    def _resolve_business_id(
        tenant_id: str,
    ) -> str:
        """
        Resolve the Business Account belonging to the tenant.

        WhatsApp configuration resolves the tenant from Meta's
        phone_number_id. CRM activity is owned by the corresponding
        Business Account.
        """

        business_id = frappe.db.get_value(
            "Business Account",
            {
                "tenant_id": tenant_id,
            },
            "business_id",
        )

        if not business_id:
            raise RuntimeError(
                f"No Business Account found for tenant '{tenant_id}'."
            )

        return business_id

    def process(
        self,
        event: IncomingMessageEvent,
        tenant_id: str | None = None,
        configuration: WhatsAppConfiguration | None = None,
    ) -> dict:

        tenant_id = (
            tenant_id
            or self._tenant_context.require()
        )

        # WhatsApp configuration is the authoritative tenant
        # source for webhook processing. Explicitly propagate it
        # into persistence so this flow does not depend on HTTP
        # TenantContext being present.
        self._activity_logger.set_tenant(
            tenant_id
        )

        if configuration is None:
            configuration = (
                self._configurations.get(
                    tenant_id
                )
            )

        if configuration is None:
            raise RuntimeError(
                f"No WhatsApp configuration found for tenant '{tenant_id}'."
            )

        if not configuration.business_id:
            raise RuntimeError(
                f"No business_id configured for WhatsApp configuration "
                f"'{configuration.configuration_id}'."
            )

        # Persist the inbound WhatsApp message before any AI,
        # CRM, calendar, or outbound processing occurs.
        #
        # This guarantees that the raw customer interaction
        # survives even when downstream processing fails.
        inbound_message = (
            event.text
            or f"[{event.message_type} message]"
        )

        self._activity_logger.log_message(
            business_id=configuration.business_id,
            related_type="WhatsApp Conversation",
            related_id=f"{tenant_id}:{event.phone_number}",
            direction=WhatsAppDirection.INBOUND,
            phone_number=event.phone_number,
            message=inbound_message,
            status="received",
            message_id=event.message_id,
        )

        if configuration is None:
            raise RuntimeError(
                f"No active WhatsApp configuration "
                f"for tenant '{tenant_id}'."
            )

        orchestration = (
            self._orchestrator.process(
                event,
                tenant_id=tenant_id,
            )
        )

        reply = (
            orchestration
            .get("response", {})
            .get("reply")
        )

        if not reply:
            return {
                "orchestration": orchestration,
                "send_result": None,
            }

        contact = WhatsAppContact(
            phone_number=event.phone_number,
            display_name=event.customer_name,
        )

        outgoing = WhatsAppMessage(
            message_id=str(uuid.uuid4()),
            conversation_id=(
                f"{tenant_id}:{event.phone_number}"
            ),
            contact=contact,
            direction=WhatsAppDirection.OUTBOUND,
            message_type=WhatsAppMessageType.TEXT,
            text=reply,
        )

        send_result = self._sender.send(
            configuration,
            outgoing,
        )

        return {
            "orchestration": orchestration,
            "send_result": send_result,
        }
