from __future__ import annotations

import hashlib
import hmac

from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
)


class WhatsAppAuthentication:
    """
    Handles authentication for the
    WhatsApp Cloud API.

    Responsibilities:

    • Authorization headers
    • Standard API headers
    • Webhook signature verification
    """

    def build_headers(
        self,
        configuration: WhatsAppConfiguration,
    ) -> dict[str, str]:

        return {

            "Authorization":
                f"Bearer {configuration.access_token}",

            "Content-Type":
                "application/json",
        }

    def compute_signature(
        self,
        configuration: WhatsAppConfiguration,
        payload: bytes,
    ) -> str:
        """
        Computes the expected
        X-Hub-Signature-256 value.
        """

        digest = hmac.new(

            configuration.app_secret.encode(),

            payload,

            hashlib.sha256,

        ).hexdigest()

        return f"sha256={digest}"

    def verify_signature(
        self,
        configuration: WhatsAppConfiguration,
        payload: bytes,
        received_signature: str,
    ) -> bool:
        """
        Validates the webhook signature.
        """

        expected = self.compute_signature(

            configuration,

            payload,

        )

        return hmac.compare_digest(

            expected,

            received_signature,

        )