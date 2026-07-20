from __future__ import annotations

from heshly_core.models.api_key import APIKey
from heshly_core.repositories.api_key_repository import (
    APIKeyRepository,
)
from heshly_core.services.security.request_signature_validator import (
    RequestSignatureValidator,
)


class WebhookVerifier:
    """
    Verifies inbound webhook requests.

    Verification includes:

    - API key lookup
    - Key status
    - Expiration
    - Request signature
    """

    def __init__(
        self,
        api_key_repository: APIKeyRepository,
        signature_validator: RequestSignatureValidator,
    ):

        self.api_key_repository = api_key_repository

        self.signature_validator = signature_validator

    # =====================================================
    # Verification
    # =====================================================

    def verify(
        self,
        key_hash: str,
        payload: str,
        signature: str,
        secret: str,
    ) -> APIKey | None:

        api_key = self.api_key_repository.get_by_hash(
            key_hash
        )

        if api_key is None:

            return None

        if not api_key.is_active:

            return None

        if api_key.is_expired:

            api_key.expire()

            self.api_key_repository.save(
                api_key
            )

            return None

        if not self.signature_validator.validate(

            secret,

            payload,

            signature,

        ):

            return None

        api_key.mark_used()

        self.api_key_repository.save(
            api_key
        )

        return api_key

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "webhook_verifier",

            "keys": self.api_key_repository.count(),

            "status": "healthy",

        }