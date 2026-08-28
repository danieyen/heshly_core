from __future__ import annotations

import hashlib
import hmac
from typing import Any

from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
)


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


class WhatsAppAuthentication:
    """
    Handles authentication for the
    WhatsApp Cloud API.

    Responsibilities:

    • Authorization headers
    • Standard API headers
    • Webhook signature verification
    Tolerant to n8n sending config as dict/JSON string.
    """

    def _normalize_config(self, configuration: Any) -> WhatsAppConfiguration:
        if isinstance(configuration, WhatsAppConfiguration):
            return configuration
        if isinstance(configuration, dict) or isinstance(configuration, str):
            data = _parse_json_if_string(configuration)
            if isinstance(data, dict):
                # Handle n8n $json.body nesting
                if "body" in data and isinstance(data["body"], dict) and "access_token" in data["body"]:
                    data = data["body"]
                if "json" in data and isinstance(data["json"], dict) and "access_token" in data["json"]:
                    data = data["json"]
                return WhatsAppConfiguration(
                    configuration_id=str(data.get("configuration_id") or data.get("configurationId") or ""),
                    tenant_id=str(data.get("tenant_id") or data.get("tenantId") or ""),
                    business_id=str(data.get("business_id") or data.get("businessId") or ""),
                    business_account_id=str(data.get("business_account_id") or data.get("businessAccountId") or ""),
                    phone_number_id=str(data.get("phone_number_id") or data.get("phoneNumberId") or ""),
                    access_token=str(data.get("access_token") or data.get("accessToken") or ""),
                    verify_token=str(data.get("verify_token") or data.get("verifyToken") or ""),
                    app_secret=str(data.get("app_secret") or data.get("appSecret") or ""),
                    display_phone_number=str(data.get("display_phone_number") or ""),
                    webhook_url=str(data.get("webhook_url") or ""),
                    language=str(data.get("language") or "en"),
                    api_version=str(data.get("api_version") or "v23.0"),
                    webhook_enabled=bool(data.get("webhook_enabled", True)),
                    business_name=str(data.get("business_name") or ""),
                )
        raise ValueError("Invalid WhatsApp configuration")

    def build_headers(
        self,
        configuration: Any,
    ) -> dict[str, str]:

        if isinstance(configuration, dict) or isinstance(configuration, str):
            configuration = self._normalize_config(configuration)

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
        configuration: Any,
        payload: bytes,
    ) -> str:
        """
        Computes the expected
        X-Hub-Signature-256 value.
        """

        if isinstance(configuration, dict) or isinstance(configuration, str):
            configuration = self._normalize_config(configuration)

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
        configuration: Any,
        payload: bytes,
        received_signature: str,
    ) -> bool:
        """
        Validates the webhook signature.
        Uses constant-time comparison to prevent timing attacks.
        Handles n8n forwarding parsed JSON vs raw bytes.
        """

        if not received_signature:
            return False

        if isinstance(configuration, dict) or isinstance(configuration, str):
            try:
                configuration = self._normalize_config(configuration)
            except ValueError:
                return False

        if not configuration or not configuration.app_secret:
            return False

        # Handle n8n sending payload as dict/JSON string instead of raw bytes
        if isinstance(payload, dict):
            import json
            payload = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        elif isinstance(payload, str) and not received_signature.startswith("sha256="):
            # If payload is string and signature is not prefixed, try raw
            payload = payload.encode("utf-8")

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
