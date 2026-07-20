from __future__ import annotations

from heshly_core.services.security.data_masking import (
    DataMasking,
)
from heshly_core.services.security.encryption_service import (
    EncryptionService,
)


class SensitiveDataProtection:
    """
    Central service for protecting sensitive data.

    Provides encryption, decryption, hashing,
    masking, and safe logging utilities.
    """

    def __init__(
        self,
        encryption_service: EncryptionService,
        masking_service: DataMasking,
    ):

        self.encryption = encryption_service

        self.masking = masking_service

    # =====================================================
    # Encryption
    # =====================================================

    def encrypt(
        self,
        value: str,
    ) -> str:

        return self.encryption.encrypt(
            value
        )

    def decrypt(
        self,
        value: str,
    ) -> str:

        return self.encryption.decrypt(
            value
        )

    # =====================================================
    # Hashing
    # =====================================================

    def hash(
        self,
        value: str,
    ) -> str:

        return self.encryption.hash(
            value
        )

    def verify_hash(
        self,
        value: str,
        digest: str,
    ) -> bool:

        return self.encryption.verify_hash(
            value,
            digest,
        )

    # =====================================================
    # Masking
    # =====================================================

    def mask_email(
        self,
        email: str,
    ) -> str:

        return self.masking.mask_email(
            email
        )

    def mask_phone(
        self,
        phone: str,
    ) -> str:

        return self.masking.mask_phone(
            phone
        )

    def mask_api_key(
        self,
        key: str,
    ) -> str:

        return self.masking.mask_api_key(
            key
        )

    def mask_secret(
        self,
        value: str,
    ) -> str:

        return self.masking.mask_secret(
            value
        )

    def sanitize(
        self,
        payload: dict,
    ) -> dict:

        return self.masking.mask_dictionary(
            payload
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "sensitive_data_protection",

            "status": "healthy",

        }