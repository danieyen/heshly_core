from __future__ import annotations

from typing import Any

from heshly_core.services.tenant.tenant_context import (
    TenantContextManager,
)


class QueryIsolation:
    """
    Query Isolation.

    Automatically scopes repository
    queries to the active tenant.
    """

    def __init__(self):

        self.context = TenantContextManager()

    # =====================================================
    # Query Scope
    # =====================================================

    def apply(
        self,
        query: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        tenant = self.context.require()

        filters = dict(query or {})

        filters["tenant_id"] = tenant.tenant_id

        return filters

    # =====================================================
    # Validation
    # =====================================================

    def validate(
        self,
        query: dict[str, Any],
    ) -> bool:

        tenant = self.context.get()

        if tenant is None:

            return False

        return (
            query.get("tenant_id")
            ==
            tenant.tenant_id
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "service": "query_isolation",

            "status": "healthy",

        }