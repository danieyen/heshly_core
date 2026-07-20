from __future__ import annotations

from heshly_core.services.security.secret_manager import (
    SecretManager,
)


class SecureConfiguration:
    """
    Secure application configuration.

    Public configuration values are stored
    separately from encrypted secrets.
    """

    def __init__(
        self,
        secret_manager: SecretManager,
    ):

        self.secret_manager = (
            secret_manager
        )

        self._config: dict[str, object] = {}

    # =====================================================
    # Configuration
    # =====================================================

    def set(
        self,
        key: str,
        value: object,
    ) -> None:

        self._config[key] = value

    def get(
        self,
        key: str,
        default: object | None = None,
    ) -> object | None:

        return self._config.get(
            key,
            default,
        )

    def exists(
        self,
        key: str,
    ) -> bool:

        return key in self._config

    def delete(
        self,
        key: str,
    ) -> bool:

        return (

            self._config.pop(
                key,
                None,
            )

            is not None

        )

    def clear(
        self,
    ) -> None:

        self._config.clear()

    def count(
        self,
    ) -> int:

        return len(
            self._config
        )

    def keys(
        self,
    ) -> list[str]:

        return sorted(
            self._config.keys()
        )

    # =====================================================
    # Secure Secrets
    # =====================================================

    def set_secret(
        self,
        name: str,
        value: str,
    ) -> None:

        self.secret_manager.set_secret(

            name,

            value,

        )

    def get_secret(
        self,
        name: str,
    ) -> str | None:

        return self.secret_manager.get_secret(
            name
        )

    def rotate_secret(
        self,
        name: str,
    ) -> str:

        return self.secret_manager.rotate_secret(
            name
        )

    def delete_secret(
        self,
        name: str,
    ) -> bool:

        return self.secret_manager.delete_secret(
            name
        )

    # =====================================================
    # Export
    # =====================================================

    def export(
        self,
    ) -> dict[str, object]:

        return dict(
            self._config
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "secure_configuration",

            "configuration_items": self.count(),

            "stored_secrets": (
                self.secret_manager.count()
            ),

            "status": "healthy",

        }