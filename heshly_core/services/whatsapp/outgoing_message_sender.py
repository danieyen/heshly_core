from __future__ import annotations

import frappe

from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
    WhatsAppMessage,
)

from heshly_core.services.crm.whatsapp_activity_logger import (
    WhatsAppActivityLogger,
)

from heshly_core.services.whatsapp.api.api_models import (
    CloudAPIError,
    CloudAPIErrorCategory,
    CloudAPISuccess,
)

from heshly_core.services.whatsapp.api.cloud_api_client import (
    WhatsAppCloudAPIClient,
)


class WhatsAppOutgoingMessageSender:
    """
    Sends outgoing WhatsApp messages and persists the resulting
    activity in Heshly CRM.

    Flow:

        WhatsAppOutgoingMessageSender
                    |
                    +--> Cloud API
                    |
                    +--> WhatsAppActivityLogger
                              |
                              +--> Heshly WhatsApp Activity
    """

    def __init__(
        self,
    ) -> None:

        self._client = WhatsAppCloudAPIClient()

        self._activity_logger = (
            WhatsAppActivityLogger()
        )

    @staticmethod
    def _resolve_business_id(
        tenant_id: str,
    ) -> str:

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

    def send(
        self,
        configuration: WhatsAppConfiguration,
        message: WhatsAppMessage,
    ) -> CloudAPISuccess | CloudAPIError:
        """
        Sends a WhatsApp message and persists the result.

        Successful sends store the real Meta message ID.

        Failed sends are also persisted so the CRM timeline reflects
        the attempted outbound communication.
        """

        # Webhook/background execution does not guarantee that
        # HTTP TenantContext is available. The WhatsApp configuration
        # is the authoritative tenant source.
        tenant_id = configuration.tenant_id

        if not tenant_id:
            raise RuntimeError(
                f"No tenant_id configured for WhatsApp configuration "
                f"{configuration.configuration_id!r}."
            )

        self._activity_logger.set_tenant(
            tenant_id
        )

        result = self._client.send_message(
            configuration,
            message,
        )

        # The WhatsApp configuration is the authoritative mapping
        # from this phone number to the Heshly Business Account.
        business_id = configuration.business_id

        if not business_id:
            raise RuntimeError(
                f"No business_id configured for WhatsApp configuration "
                f"'{configuration.configuration_id}'."
            )

        related_id = message.conversation_id

        message_id = message.message_id

        status = "failed"

        if isinstance(result, CloudAPISuccess):
            # FIX: Do NOT treat success without Meta ID as sent. Hide-behind-success bug.
            # A 200 without messages[0].id is NOT proof of delivery.
            if not result.message_id:
                try:
                    import frappe as _f
                    _f.logger("heshly_whatsapp_router").error(
                        "outbound CloudAPISuccess missing Meta message ID — treating as FAILED phone_number_id=%s to=%s metadata=%s",
                        getattr(configuration, "phone_number_id", ""), message.contact.phone_number[:6] + "***" if getattr(message, "contact", None) else "***", str(result.metadata)[:500],
                    )
                except Exception:
                    pass
                status = "failed"
                # persist as failed, return error wrapper so caller knows
                err = CloudAPIError(
                    code=-2,
                    message="Meta response missing message ID (not delivered)",
                    category=CloudAPIErrorCategory.SERVER,
                    retryable=False,
                    error_type="MissingMessageId",
                )
                self._activity_logger.log_message(
                    business_id=business_id,
                    related_type="WhatsApp Conversation",
                    related_id=related_id,
                    direction=message.direction,
                    phone_number=message.contact.phone_number,
                    message=message.text or "",
                    status=status,
                    message_id=message_id,
                )
                return err
            status = "sent"
            # Meta's actual WhatsApp message ID is authoritative.
            if result.message_id:
                message_id = result.message_id

        if isinstance(result, CloudAPIError):
            try:
                import frappe as _f
                _f.logger("heshly_whatsapp_router").error(
                    "outbound Meta error phone_number_id=%s to=%s code=%s type=%s message=%s",
                    getattr(configuration, "phone_number_id", ""), message.contact.phone_number[:6] + "***" if getattr(message, "contact", None) else "***",
                    getattr(result, "code", ""), getattr(result, "error_type", ""), (getattr(result, "message", "") or "")[:400],
                )
            except Exception:
                pass

        self._activity_logger.log_message(
            business_id=business_id,
            related_type="WhatsApp Conversation",
            related_id=related_id,
            direction=message.direction,
            phone_number=message.contact.phone_number,
            message=message.text or "",
            status=status,
            message_id=message_id,
        )

        return result
