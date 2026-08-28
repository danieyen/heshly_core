from __future__ import annotations

from typing import Generic, TypeVar, Any

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)

from heshly_core.services.tenant.tenant_permission_manager import (
    TenantPermissionManager,
)


T = TypeVar("T")


def _parse_json_if_string(value: Any) -> Any:
    if isinstance(value, str):
        import json
        value = value.strip()
        if value.startswith("{") and value.endswith("}"):
            try:
                return json.loads(value)
            except Exception:
                return value
    return value


class BaseRepository(Generic[T]):
    """
    Base class for tenant-aware repositories.

    TenantContext contains the canonical tenant_id.

    business_id and tenant_id are deliberately
    different concepts. All queries must be tenant-filtered.
    Tolerant to n8n sending tenant_id nested under body/json.
    """

    def __init__(self):

        self.context = TenantContext()

        self.permission = TenantPermissionManager()

    # =====================================================
    # Current Tenant
    # =====================================================

    def current_tenant(self) -> str:

        return self.context.require()

    def _extract_tenant_id(self, tenant_id: Any) -> str | None:
        if tenant_id is None:
            return None
        if isinstance(tenant_id, dict):
            for key in ("tenant_id", "tenantId", "tenant", "body", "json"):
                if key in tenant_id:
                    val = tenant_id[key]
                    if isinstance(val, str) and val.strip():
                        return val.strip()
                    if isinstance(val, dict):
                        for k2 in ("tenant_id", "tenantId"):
                            if k2 in val and isinstance(val[k2], str) and val[k2].strip():
                                return val[k2].strip()
            return None
        if isinstance(tenant_id, str):
            parsed = _parse_json_if_string(tenant_id)
            if isinstance(parsed, dict):
                return self._extract_tenant_id(parsed)
            return tenant_id.strip() if tenant_id.strip() else None
        return str(tenant_id).strip() if str(tenant_id).strip() else None

    # =====================================================
    # Require Tenant Access
    # =====================================================

    def require_tenant(
        self,
        tenant_id: Any = None,
    ) -> str:

        if tenant_id is None:
            tenant_id = self.current_tenant()
        else:
            # Handle n8n wrapping
            extracted = self._extract_tenant_id(tenant_id)
            if extracted:
                tenant_id = extracted
            else:
                # Try context fallback
                try:
                    tenant_id = self.current_tenant()
                except RuntimeError:
                    raise ValueError("tenant_id is required - tenant resolution failed. Ensure n8n Workflow Inputs include tenant_id.")

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
        tenant_id: Any = None,
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
        filters: dict | Any = None,
    ) -> dict:

        # Handle n8n sending JSON string
        filters = _parse_json_if_string(filters)
        if filters is None:
            filters = {}
        if isinstance(filters, str):
            filters = {}
        if not isinstance(filters, dict):
            filters = {}

        # Handle n8n wrapping
        if "body" in filters and isinstance(filters["body"], dict) and "tenant_id" not in filters:
            # Check if body contains tenant_id
            if "tenant_id" in filters["body"] or "tenantId" in filters["body"]:
                filters = {**filters, **filters["body"]}

        result = dict(filters)

        # Do not allow caller to override tenant_id
        if "tenant_id" in result:
            # Ensure it matches current tenant
            requested = self._extract_tenant_id(result["tenant_id"])
            if not requested:
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
