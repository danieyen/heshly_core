from __future__ import annotations

import base64
import hashlib
import secrets
from itertools import cycle


class EncryptionService:
    """
    Encryption service.

    NOTE:
    This implementation is intended for
    development and testing.

    Replace with a proper encryption
    backend (AES/Fernet/KMS) in
    production.
    """

    def __init__(
        self,
        secret: str,
    ):

        self.secret = secret.encode()

    # =====================================================
    # Internal
    # =====================================================

    def _key(self) -> bytes:

        return hashlib.sha256(
            self.secret
        ).digest()

    # =====================================================
    # Encrypt
    # =====================================================

    def encrypt(
        self,
        plaintext: str,
    ) -> str:

        data = plaintext.encode()

        encrypted = bytes(

            value ^ key

            for value, key in zip(

                data,

                cycle(self._key())

            )

        )

        return base64.urlsafe_b64encode(

            encrypted

        ).decode()

    # =====================================================
    # Decrypt
    # =====================================================

    def decrypt(
        self,
        ciphertext: str,
    ) -> str:

        encrypted = base64.urlsafe_b64decode(
            ciphertext
        )

        decrypted = bytes(

            value ^ key

            for value, key in zip(

                encrypted,

                cycle(self._key())

            )

        )

        return decrypted.decode()

    # =====================================================
    # Hash
    # =====================================================

    def hash(
        self,
        value: str,
    ) -> str:

        return hashlib.sha256(
            value.encode()
        ).hexdigest()

    # =====================================================
    # Verify Hash
    # =====================================================

    def verify_hash(
        self,
        value: str,
        digest: str,
    ) -> bool:

        return self.hash(
            value
        ) == digest

    # =====================================================
    # Random Secret
    # =====================================================

    def generate_secret(
        self,
        length: int = 32,
    ) -> str:

        return secrets.token_urlsafe(
            length
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "encryption_service",

            "algorithm": "SHA256 + XOR (development)",

            "status": "healthy",

        }