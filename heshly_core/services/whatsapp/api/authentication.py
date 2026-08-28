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

        if not configuration or not configuration.access_token:
            raise ValueError("access_token is required to build headers")

        token = configuration.access_token.strip()
        if not token:
            raise ValueError("access_token must be non-empty")

        return {

            "Authorization":
                f"Bearer {token}",

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

        if not configuration or not configuration.app_secret:
            raise ValueError("app_secret is required to compute signature")

        if payload is None:
            payload = b""

        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        digest = hmac.new(

            configuration.app_secret.encode("utf-8"),

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
        Uses constant-time comparison to prevent timing attacks.
        """

        if not received_signature:
            return False

        if not configuration or not configuration.app_secret:
            return False

        try:
            expected = self.compute_signature(

                configuration,

                payload,

            )
        except ValueError:
            return False

        # Normalize: Meta sends "sha256=..."
        # Ensure both are strings for compare_digest
        if not isinstance(received_signature, str):
            received_signature = str(received_signature)

        return hmac.compare_digest(

            expected,

            received_signature,

        )
