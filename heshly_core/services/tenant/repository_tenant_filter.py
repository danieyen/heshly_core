from __future__ import annotations

from typing import Any

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)


class RepositoryTenantFilter:
    """
    Repository Tenant Filter.

    Filters repository records so that
    only data belonging to the active
    tenant is returned.
    """

    def __init__(self):

        self.context = TenantContext()

    # =====================================================
    # Filtering
    # =====================================================

    def filter(
        self,
        records: list[Any],
    ) -> list[Any]:

        tenant = self.context.require()

        return [

            record

            for record in records

            if getattr(
                record,
                "tenant_id",
                None,
            )
            == tenant

        ]

    # =====================================================
    # Validation
    # =====================================================

    def validate(
        self,
        record: Any,
    ) -> bool:

        tenant = self.context.get()

        if tenant is None:

            return False

        return (

            getattr(
                record,
                "tenant_id",
                None,
            )

            ==

            tenant

        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "repository_tenant_filter",

            "status": "healthy",

        }