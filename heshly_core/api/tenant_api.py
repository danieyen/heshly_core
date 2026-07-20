from __future__ import annotations

from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.services.admin.tenant_administration import (
    TenantAdministration,
)


class TenantAPI:
    """
    Tenant API Layer.

    Provides tenant operations
    through a service interface.
    """

    def __init__(self):

        self.service = TenantAdministration()


    # =====================================================
    # Create Tenant
    # =====================================================

    def create(
        self,
        tenant: Tenant,
    ) -> Tenant:

        return self.service.register(
            tenant
        )


    # =====================================================
    # Get Tenant
    # =====================================================

    def get(
        self,
        tenant_id: str,
    ) -> Tenant | None:

        return self.service.get(
            tenant_id
        )


    # =====================================================
    # List Tenants
    # =====================================================

    def list(self):

        return self.service.list()


    # =====================================================
    # Suspend Tenant
    # =====================================================

    def suspend(
        self,
        tenant_id: str,
    ) -> bool:

        return self.service.suspend(
            tenant_id
        )


    # =====================================================
    # Activate Tenant
    # =====================================================

    def activate(
        self,
        tenant_id: str,
    ) -> bool:

        return self.service.activate(
            tenant_id
        )


    # =====================================================
    # Delete Tenant
    # =====================================================

    def delete(
        self,
        tenant_id: str,
    ) -> bool:

        return self.service.remove(
            tenant_id
        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "api":
                "tenant_api",

            "status":
                "healthy",

        }