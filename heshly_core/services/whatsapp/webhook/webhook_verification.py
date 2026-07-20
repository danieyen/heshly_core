from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
)

from heshly_core.services.whatsapp.api.authentication import (
    WhatsAppAuthentication,
)

from heshly_core.services.whatsapp.webhook.webhook_models import (
    WebhookVerificationRequest,
    WebhookVerificationResult,
)


class WhatsAppWebhookVerification:
    """
    Handles WhatsApp webhook verification.

    Responsibilities

    • Verify Meta GET challenge
    • Verify POST signatures
    """

    def __init__(self) -> None:

        self._authentication = (
            WhatsAppAuthentication()
        )

    def verify_challenge(
        self,
        configuration: WhatsAppConfiguration,
        request: WebhookVerificationRequest,
    ) -> WebhookVerificationResult:

        if request.mode != "subscribe":

            return WebhookVerificationResult(

                success=False,

                message="Invalid verification mode.",

            )

        if (
            request.verify_token
            != configuration.verify_token
        ):

            return WebhookVerificationResult(

                success=False,

                message="Invalid verify token.",

            )

        return WebhookVerificationResult(

            success=True,

            challenge=request.challenge,

            message="Verification successful.",

        )

    def verify_signature(
        self,
        configuration: WhatsAppConfiguration,
        payload: bytes,
        signature: str,
    ) -> bool:

        return (
            self._authentication
            .verify_signature(

                configuration,

                payload,

                signature,

            )
        )