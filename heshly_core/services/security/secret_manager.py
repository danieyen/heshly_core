from __future__ import annotations

from heshly_core.services.security.encryption_service import (
    EncryptionService,
)


class SecretManager:
    """
    Stores encrypted application secrets.

    Secrets are encrypted before storage
    and decrypted only when requested.
    """

    def __init__(
        self,
        encryption_service: EncryptionService,
    ):

        self.encryption_service = (
            encryption_service
        )

        self._secrets: dict[str, str] = {}

    # =====================================================
    # CRUD
    # =====================================================

    def set_secret(
        self,
        name: str,
        value: str,
    ) -> None:

        encrypted = (
            self.encryption_service.encrypt(
                value
            )
        )

        self._secrets[name] = encrypted

    def get_secret(
        self,
        name: str,
    ) -> str | None:

        encrypted = self._secrets.get(
            name
        )

        if encrypted is None:

            return None

        return (
            self.encryption_service.decrypt(
                encrypted
            )
        )

    def delete_secret(
        self,
        name: str,
    ) -> bool:

        return (

            self._secrets.pop(
                name,
                None,
            )

            is not None

        )

    def exists(
        self,
        name: str,
    ) -> bool:

        return name in self._secrets

    def list_names(
        self,
    ) -> list[str]:

        return sorted(
            self._secrets.keys()
        )

    def count(
        self,
    ) -> int:

        return len(
            self._secrets
        )

    def clear(
        self,
    ) -> None:

        self._secrets.clear()

    # =====================================================
    # Rotation
    # =====================================================

    def rotate_secret(
        self,
        name: str,
    ) -> str:

        new_secret = (
            self.encryption_service.generate_secret()
        )

        self.set_secret(
            name,
            new_secret,
        )

        return new_secret

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "secret_manager",

            "stored_secrets": self.count(),

            "status": "healthy",

        }