from __future__ import annotations

import hashlib
import hmac


class RequestSignatureValidator:
    """
    Validates HMAC request signatures.

    Used for securing inbound webhooks
    and API requests.
    """

    def __init__(
        self,
        algorithm: str = "sha256",
    ):

        self.algorithm = algorithm

    # =====================================================
    # Signature Generation
    # =====================================================

    def generate(
        self,
        secret: str,
        payload: str,
    ) -> str:

        digest = hmac.new(

            secret.encode(),

            payload.encode(),

            getattr(hashlib, self.algorithm),

        )

        return digest.hexdigest()

    # =====================================================
    # Validation
    # =====================================================

    def validate(
        self,
        secret: str,
        payload: str,
        signature: str,
    ) -> bool:

        expected = self.generate(

            secret,

            payload,

        )

        return hmac.compare_digest(

            expected,

            signature,

        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "request_signature_validator",

            "algorithm": self.algorithm,

            "status": "healthy",

        }