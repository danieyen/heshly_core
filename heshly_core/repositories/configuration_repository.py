from __future__ import annotations

from heshly_core.models.tenant_configuration import (
    TenantConfiguration,
)


class ConfigurationRepository:
    """
    Tenant Configuration Repository.

    Responsible for persisting tenant
    configuration objects.
    """

    def __init__(self):

        self._configurations: dict[
            str,
            TenantConfiguration,
        ] = {}

    # =====================================================
    # CRUD
    # =====================================================

    def save(
        self,
        configuration: TenantConfiguration,
    ) -> TenantConfiguration:

        self._configurations[
            configuration.tenant_id
        ] = configuration

        return configuration

    def get(
        self,
        tenant_id: str,
    ) -> TenantConfiguration | None:

        return self._configurations.get(
            tenant_id
        )

    def exists(
        self,
        tenant_id: str,
    ) -> bool:

        return (
            tenant_id
            in
            self._configurations
        )

    def delete(
        self,
        tenant_id: str,
    ) -> bool:

        if tenant_id not in self._configurations:

            return False

        del self._configurations[
            tenant_id
        ]

        return True

    # =====================================================
    # Listing
    # =====================================================

    def all(
        self,
    ) -> list[TenantConfiguration]:

        return list(
            self._configurations.values()
        )

    def count(self) -> int:

        return len(
            self._configurations
        )

    def clear(self):

        self._configurations.clear()

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "repository": "configuration",

            "configurations": self.count(),

            "status": "healthy",

        }