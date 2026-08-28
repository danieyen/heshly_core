from __future__ import annotations

from typing import Generic, TypeVar

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)

from heshly_core.services.tenant.tenant_permission_manager import (
    TenantPermissionManager,
)


T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Base class for tenant-aware repositories.

    TenantContext contains the canonical tenant_id.

    business_id and tenant_id are deliberately
    different concepts. All queries must be tenant-filtered.
    """

    def __init__(self):

        self.context = TenantContext()

        self.permission = TenantPermissionManager()

    # =====================================================
    # Current Tenant
    # =====================================================

    def current_tenant(self) -> str:

        return self.context.require()

    # =====================================================
    # Require Tenant Access
    # =====================================================

    def require_tenant(
        self,
        tenant_id: str | None = None,
    ) -> str:

        if tenant_id is None:
            tenant_id = self.current_tenant()

        if not tenant_id or not str(tenant_id).strip():
            raise ValueError("tenant_id is required")

        tenant_id = str(tenant_id).strip()

        self.permission.require_tenant(
            tenant_id
        )

        return tenant_id

    # =====================================================
    # Tenant Filter
    # =====================================================

    def tenant_filter(
        self,
        tenant_id: str | None = None,
    ) -> dict:

        return {
            "tenant_id": self.require_tenant(
                tenant_id
            )
        }

    # =====================================================
    # Apply Tenant Filter
    # =====================================================

    def apply_tenant_filter(
        self,
        filters: dict | None = None,
    ) -> dict:

        result = dict(filters or {})

        # Do not allow caller to override tenant_id
        if "tenant_id" in result:
            # Ensure it matches current tenant
            requested = str(result["tenant_id"]).strip()
            required = self.require_tenant()
            if requested != required:
                raise PermissionError(
                    f"Cross-tenant access denied: requested {requested} != current {required}"
                )

        result.update(
            self.tenant_filter()
        )

        return result

    # =====================================================
    # Access Check
    # =====================================================

    def can_access(
        self,
        tenant_id: str,
    ) -> bool:

        return self.permission.can_access_tenant(
            tenant_id
        )

    # =====================================================
    # Tenant Exists
    # =====================================================

    def has_tenant(self) -> bool:

        return self.context.has_context()

    # =====================================================
    # Clear
    # =====================================================

    def clear(self):

        self.context.clear()

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {
            "repository": self.__class__.__name__,
            "status": "healthy",
            "tenant": self.has_tenant(),
            "admin": self.permission.is_system_admin(),
        }
