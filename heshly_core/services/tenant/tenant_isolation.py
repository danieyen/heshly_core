from __future__ import annotations


from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContextManager,
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

        self.context = TenantContextManager()



    # =====================================================
    # Current Tenant Validation
    # =====================================================

    def require_tenant(self) -> Tenant:

        tenant = self.context.get()


        if tenant is None:

            raise PermissionError(
                "Tenant context required"
            )


        return tenant



    # =====================================================
    # Resource Ownership
    # =====================================================

    def validate_owner(
        self,
        resource,
    ) -> bool:


        tenant = self.require_tenant()


        resource_tenant_id = getattr(
            resource,
            "tenant_id",
            None,
        )


        if resource_tenant_id is None:

            raise PermissionError(
                "Resource has no tenant ownership"
            )


        if resource_tenant_id != tenant.tenant_id:

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


        tenant = self.require_tenant()


        return tenant.tenant_id == tenant_id



    # =====================================================
    # Access Check
    # =====================================================

    def can_access(
        self,
        resource,
    ) -> bool:


        try:

            return self.validate_owner(
                resource
            )


        except PermissionError:

            return False



    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "tenant_isolation",

            "status": "healthy",

        }