from __future__ import annotations

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)


class TenantIsolation:
    """
    Tenant Isolation Rules.

    Enforces tenant boundaries.

    Responsibilities:

    - Validate tenant context
    - Validate resource ownership
    - Prevent cross-tenant access

    Used by:

    - CRM
    - Calendar
    - AI
    - Analytics
    - Payments
    """

    def __init__(self):
        self.context = TenantContext()

    # =====================================================
    # Current Tenant Validation
    # =====================================================

    def require_tenant(self) -> str:
        """
        Return the canonical tenant_id for the
        current execution context.

        Raises:
            PermissionError: if no tenant context exists.
        """

        try:
            return self.context.require()

        except RuntimeError as exc:
            raise PermissionError(
                "Tenant context required"
            ) from exc

    # =====================================================
    # Resource Ownership
    # =====================================================

    def validate_owner(
        self,
        resource,
    ) -> bool:
        """
        Validate that a resource belongs to
        the current tenant.
        """

        tenant_id = self.require_tenant()

        resource_tenant_id = getattr(
            resource,
            "tenant_id",
            None,
        )

        if resource_tenant_id is None:
            raise PermissionError(
                "Resource has no tenant ownership"
            )

        if resource_tenant_id != tenant_id:
            raise PermissionError(
                "Cross tenant access denied"
            )

        return True

    # =====================================================
    # Tenant Match
    # =====================================================

    def same_tenant(
        self,
        tenant_id: str,
    ) -> bool:
        """
        Check whether the supplied tenant_id
        matches the active tenant.
        """

        current_tenant_id = self.require_tenant()

        return current_tenant_id == tenant_id

    # =====================================================
    # Access Check
    # =====================================================

    def can_access(
        self,
        resource,
    ) -> bool:
        """
        Return True only when the resource belongs
        to the current tenant.
        """

        try:
            return self.validate_owner(resource)

        except PermissionError:
            return False

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:
        """
        Return tenant isolation health information.
        """

        return {
            "service": "tenant_isolation",
            "status": "healthy",
            "has_context": self.context.has_context(),
            "tenant": self.context.get(),
        }
