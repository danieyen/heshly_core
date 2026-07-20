from __future__ import annotations

from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.repositories.tenant_admin_repository import (
    TenantAdministrationRepository,
)


class TenantSearch:
    """
    Platform Tenant Search Service.
    """

    def __init__(self):

        self.repository = (
            TenantAdministrationRepository()
        )

    # =====================================================
    # Search
    # =====================================================

    def search(
        self,
        query: str,
    ) -> list[Tenant]:

        query = query.lower()

        results = []

        for tenant in self.repository.list():

            if (

                query in tenant.tenant_id.lower()

                or

                query in tenant.name.lower()

                or

                (
                    tenant.email
                    and query in tenant.email.lower()
                )

                or

                (
                    tenant.phone
                    and query in tenant.phone.lower()
                )

            ):

                results.append(
                    tenant
                )

        return results


    # =====================================================
    # Filter by Status
    # =====================================================

    def filter_by_status(
        self,
        status,
    ) -> list[Tenant]:

        return [

            tenant

            for tenant in self.repository.list()

            if tenant.status == status

        ]


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "tenant_search",

            "status": "healthy",

        }