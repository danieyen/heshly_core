from __future__ import annotations

from heshly_core.models.tenant import (
    Tenant,
    TenantStatus,
)


class TenantRepository:
    """
    Tenant Repository.

    Handles tenant persistence operations.

    Current implementation:
        In-memory storage

    Future:
        ERPNext DocType storage
        Database persistence
    """


    def __init__(self):

        self.tenants: dict[str, Tenant] = {}


    # =====================================================
    # Create / Save
    # =====================================================

    def save(
        self,
        tenant: Tenant,
    ) -> Tenant:

        self.tenants[
            tenant.tenant_id
        ] = tenant

        return tenant


    # =====================================================
    # Retrieve
    # =====================================================

    def get(
        self,
        tenant_id: str,
    ) -> Tenant | None:

        return self.tenants.get(
            tenant_id
        )


    # =====================================================
    # List
    # =====================================================

    def all(self) -> list[Tenant]:

        return list(
            self.tenants.values()
        )


    # =====================================================
    # Status Queries
    # =====================================================

    def active(self) -> list[Tenant]:

        return [

            tenant

            for tenant in self.tenants.values()

            if tenant.status == TenantStatus.ACTIVE

        ]


    def trial(self) -> list[Tenant]:

        return [

            tenant

            for tenant in self.tenants.values()

            if tenant.status == TenantStatus.TRIAL

        ]


    # =====================================================
    # Delete
    # =====================================================

    def delete(
        self,
        tenant_id: str,
    ) -> bool:


        if tenant_id not in self.tenants:

            return False


        del self.tenants[
            tenant_id
        ]


        return True


    # =====================================================
    # Search
    # =====================================================

    def find_by_name(
        self,
        name: str,
    ) -> list[Tenant]:

        search = name.lower()


        return [

            tenant

            for tenant in self.tenants.values()

            if search in tenant.name.lower()

        ]


    # =====================================================
    # Utilities
    # =====================================================

    def clear(self):

        self.tenants.clear()


    def count(self) -> int:

        return len(
            self.tenants
        )


    def summary(self) -> dict:

        return {

            "total": self.count(),

            "active": len(
                self.active()
            ),

            "trial": len(
                self.trial()
            ),

        }