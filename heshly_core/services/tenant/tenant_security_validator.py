from __future__ import annotations

from typing import Any

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)


class TenantSecurityValidator:
    """
    Tenant Security Validator.

    Performs security validation before
    tenant resources are accessed.

    Used by:

    • CRM
    • Calendar
    • Analytics
    • AI
    • Payments
    """

    def __init__(self):

        self.context = TenantContext()

    # =====================================================
    # Context Validation
    # =====================================================

    def validate_context(self) -> bool:

        return self.context.has_context()

    # =====================================================
    # Resource Validation
    # =====================================================

    def validate_resource(
        self,
        resource: Any,
    ) -> bool:

        tenant = self.context.require()

        return (

            getattr(
                resource,
                "tenant_id",
                None,
            )

            ==

            tenant

        )

    # =====================================================
    # Query Validation
    # =====================================================

    def validate_query(
        self,
        query: dict[str, Any],
    ) -> bool:

        tenant = self.context.require()

        return (

            query.get(
                "tenant_id"
            )

            ==

            tenant

        )

    # =====================================================
    # Full Validation
    # =====================================================

    def validate(
        self,
        resource: Any | None = None,
        query: dict[str, Any] | None = None,
    ) -> bool:

        if not self.validate_context():

            return False

        if resource is not None:

            if not self.validate_resource(
                resource
            ):

                return False

        if query is not None:

            if not self.validate_query(
                query
            ):

                return False

        return True

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "service": "tenant_security_validator",

            "status": "healthy",

            "context": self.context.has_context(),

        }