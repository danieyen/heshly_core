from __future__ import annotations

from typing import Any

from heshly_core.models.tenant_configuration import (
    TenantConfiguration,
)

from heshly_core.repositories.configuration_repository import (
    ConfigurationRepository,
)


class ConfigurationManager:
    """
    Configuration Manager.

    Central service responsible for managing
    tenant configuration.

    Used by:

    • AI
    • CRM
    • Calendar
    • Analytics
    • Marketing
    • Business
    """

    def __init__(self):

        self.repository = ConfigurationRepository()

    # =====================================================
    # Configuration
    # =====================================================

    def create(
        self,
        tenant_id: str,
    ) -> TenantConfiguration:

        configuration = TenantConfiguration(

            tenant_id=tenant_id,

        )

        self.repository.save(
            configuration
        )

        return configuration

    def get(
        self,
        tenant_id: str,
    ) -> TenantConfiguration | None:

        return self.repository.get(
            tenant_id
        )

    def get_or_create(
        self,
        tenant_id: str,
    ) -> TenantConfiguration:

        configuration = self.get(
            tenant_id
        )

        if configuration is None:

            configuration = self.create(
                tenant_id
            )

        return configuration

    # =====================================================
    # Settings
    # =====================================================

    def set(
        self,
        tenant_id: str,
        key: str,
        value: Any,
        description: str = "",
    ) -> TenantConfiguration:

        configuration = self.get_or_create(
            tenant_id
        )

        configuration.set(

            key=key,

            value=value,

            description=description,

        )

        self.repository.save(
            configuration
        )

        return configuration

    def value(
        self,
        tenant_id: str,
        key: str,
        default: Any = None,
    ) -> Any:

        configuration = self.get(
            tenant_id
        )

        if configuration is None:

            return default

        return configuration.get(
            key,
            default,
        )

    def remove(
        self,
        tenant_id: str,
        key: str,
    ) -> bool:

        configuration = self.get(
            tenant_id
        )

        if configuration is None:

            return False

        removed = configuration.remove(
            key
        )

        self.repository.save(
            configuration
        )

        return removed

    # =====================================================
    # Repository
    # =====================================================

    def exists(
        self,
        tenant_id: str,
    ) -> bool:

        return self.repository.exists(
            tenant_id
        )

    def all(
        self,
    ) -> list[TenantConfiguration]:

        return self.repository.all()

    def clear(self):

        self.repository.clear()

    # =====================================================
    # Helpers
    # =====================================================

    def summary(self) -> dict:

        return {

            "configurations": self.repository.count(),

            "health": self.health(),

        }

    def health(self) -> dict:

        return {

            "service": "configuration_manager",

            "repository": True,

            "status": "healthy",

        }