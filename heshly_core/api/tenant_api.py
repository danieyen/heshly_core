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
    All operations enforce tenant isolation via TenantContext.
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

        if tenant is None:
            raise ValueError("tenant is required")

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

        if not tenant_id or not str(tenant_id).strip():
            raise ValueError("tenant_id is required")

        return self.service.get(
            str(tenant_id).strip()
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

        if not tenant_id or not str(tenant_id).strip():
            raise ValueError("tenant_id is required")

        return self.service.suspend(
            str(tenant_id).strip()
        )


    # =====================================================
    # Activate Tenant
    # =====================================================

    def activate(
        self,
        tenant_id: str,
    ) -> bool:

        if not tenant_id or not str(tenant_id).strip():
            raise ValueError("tenant_id is required")

        return self.service.activate(
            str(tenant_id).strip()
        )


    # =====================================================
    # Delete Tenant
    # =====================================================

    def delete(
        self,
        tenant_id: str,
    ) -> bool:

        if not tenant_id or not str(tenant_id).strip():
            raise ValueError("tenant_id is required")

        return self.service.remove(
            str(tenant_id).strip()
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
