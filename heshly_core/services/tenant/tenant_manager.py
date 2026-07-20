from __future__ import annotations

from datetime import datetime, UTC

from heshly_core.models.tenant import (
    Tenant,
    TenantStatus,
)

from heshly_core.repositories.tenant_repository import (
    TenantRepository,
)


class TenantManager:
    """
    Tenant Manager.

    Handles tenant lifecycle and business rules.

    Responsibilities:

    - Create tenants
    - Manage tenant status
    - Validate tenants
    - Retrieve tenant context
    - Coordinate repository operations
    """

    def __init__(self):

        self.repository = TenantRepository()


    # =====================================================
    # Create Tenant
    # =====================================================

    def create(
        self,
        tenant: Tenant,
    ) -> Tenant:

        existing = self.repository.get(
            tenant.tenant_id
        )

        if existing:

            raise ValueError(
                "Tenant already exists"
            )


        return self.repository.save(
            tenant
        )


    # =====================================================
    # Retrieve
    # =====================================================

    def get(
        self,
        tenant_id: str,
    ) -> Tenant | None:

        return self.repository.get(
            tenant_id
        )


    def all(self) -> list[Tenant]:

        return self.repository.all()


    # =====================================================
    # Lifecycle
    # =====================================================

    def activate(
        self,
        tenant_id: str,
    ) -> Tenant:


        tenant = self._require(
            tenant_id
        )


        tenant.activate()


        return self.repository.save(
            tenant
        )


    def suspend(
        self,
        tenant_id: str,
    ) -> Tenant:


        tenant = self._require(
            tenant_id
        )


        tenant.suspend()


        return self.repository.save(
            tenant
        )


    def delete(
        self,
        tenant_id: str,
    ) -> Tenant:


        tenant = self._require(
            tenant_id
        )


        tenant.delete()


        return self.repository.save(
            tenant
        )


    # =====================================================
    # Validation
    # =====================================================

    def is_active(
        self,
        tenant_id: str,
    ) -> bool:


        tenant = self.get(
            tenant_id
        )


        if not tenant:

            return False


        return tenant.status == TenantStatus.ACTIVE



    def validate(
        self,
        tenant_id: str,
    ) -> bool:


        tenant = self.get(
            tenant_id
        )


        if not tenant:

            return False


        return tenant.status not in [

            TenantStatus.DELETED,

            TenantStatus.INACTIVE,

        ]


    # =====================================================
    # Search
    # =====================================================

    def search(
        self,
        name: str,
    ) -> list[Tenant]:

        return self.repository.find_by_name(
            name
        )


    # =====================================================
    # Summary
    # =====================================================

    def summary(self) -> dict:

        return self.repository.summary()


    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "service": "tenant_manager",

            "repository": True,

            "status": "healthy",

        }


    # =====================================================
    # Internal
    # =====================================================

    def _require(
        self,
        tenant_id: str,
    ) -> Tenant:


        tenant = self.get(
            tenant_id
        )


        if not tenant:

            raise ValueError(
                f"Tenant {tenant_id} not found"
            )


        return tenant