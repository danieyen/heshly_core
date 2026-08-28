from __future__ import annotations

from typing import Any

from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.services.admin.tenant_administration import (
    TenantAdministration,
)

from heshly_core.services.tenant.tenant_context import TenantContext


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


def _extract_payload(payload: Any) -> dict:
    payload = _parse_json_if_string(payload)
    if isinstance(payload, dict):
        if "body" in payload and isinstance(payload["body"], dict):
            body = payload["body"]
            if any(k in body for k in ("tenant_id", "tenantId", "name", "id")):
                return body
        if "json" in payload and isinstance(payload["json"], dict):
            inner = payload["json"]
            if any(k in inner for k in ("tenant_id", "tenantId")):
                return inner
    if isinstance(payload, dict):
        return payload
    return {}


class TenantAPI:
    """
    Tenant API Layer.

    Provides tenant operations
    through a service interface.
    All operations enforce tenant isolation via TenantContext.
    Tolerant to n8n wrapping and JSON strings.
    """

    def __init__(self, tenant_context: TenantContext | None = None):

        self.service = TenantAdministration()
        self.tenant_context = tenant_context or TenantContext()


    # =====================================================
    # Create Tenant
    # =====================================================

    def create(
        self,
        tenant: Tenant | dict | str,
    ) -> Tenant:

        if isinstance(tenant, dict) or isinstance(tenant, str):
            data = _extract_payload(tenant)
            if isinstance(data, dict) and "tenant" in data and isinstance(data["tenant"], dict):
                data = data["tenant"]
            # Build Tenant from dict
            tenant = Tenant(
                tenant_id=str(data.get("tenant_id") or data.get("tenantId") or data.get("id") or ""),
                name=str(data.get("name") or data.get("tenant_name") or ""),
                status=data.get("status") or "active",
            )

        if tenant is None:
            raise ValueError("tenant is required")

        result = self.service.register(
            tenant
        )
        # Set context to new tenant
        try:
            self.tenant_context.set(result.tenant_id)
        except Exception:
            pass
        return result


    # =====================================================
    # Get Tenant
    # =====================================================

    def get(
        self,
        tenant_id: Any,
    ) -> Tenant | None:

        # Handle n8n wrapping
        if isinstance(tenant_id, dict) or isinstance(tenant_id, str) and tenant_id.strip().startswith("{"):
            data = _extract_payload(tenant_id)
            tenant_id = data.get("tenant_id") or data.get("tenantId") or data.get("id") or tenant_id

        if isinstance(tenant_id, dict):
            tenant_id = tenant_id.get("tenant_id") or tenant_id.get("tenantId") or ""

        if not tenant_id or not str(tenant_id).strip():
            raise ValueError("tenant_id is required")

        tenant_id = str(tenant_id).strip()

        # Handle JSON string
        parsed = _parse_json_if_string(tenant_id)
        if isinstance(parsed, dict):
            tenant_id = str(parsed.get("tenant_id") or parsed.get("tenantId") or tenant_id).strip()

        return self.service.get(
            tenant_id
        )


    # =====================================================
    # List Tenants
    # =====================================================

    def list(self, payload: Any = None):

        # Handle n8n passing payload
        if payload is not None:
            data = _extract_payload(payload)
            tenant_id = data.get("tenant_id") or data.get("tenantId")
            if tenant_id:
                try:
                    self.tenant_context.set(str(tenant_id).strip())
                except Exception:
                    pass

        return self.service.list()


    # =====================================================
    # Suspend Tenant
    # =====================================================

    def suspend(
        self,
        tenant_id: Any,
    ) -> bool:

        if isinstance(tenant_id, dict) or isinstance(tenant_id, str) and tenant_id.strip().startswith("{"):
            data = _extract_payload(tenant_id)
            tenant_id = data.get("tenant_id") or data.get("tenantId") or tenant_id

        if isinstance(tenant_id, dict):
            tenant_id = tenant_id.get("tenant_id") or tenant_id.get("tenantId") or ""

        if not tenant_id or not str(tenant_id).strip():
            raise ValueError("tenant_id is required")

        return self.service.suspend(
            str(tenant_id).strip()
        )


    # =====================================================
    # Activate Tenant
    # =====================================================

    def activate(
        self,
        tenant_id: Any,
    ) -> bool:

        if isinstance(tenant_id, dict) or isinstance(tenant_id, str) and tenant_id.strip().startswith("{"):
            data = _extract_payload(tenant_id)
            tenant_id = data.get("tenant_id") or data.get("tenantId") or tenant_id

        if isinstance(tenant_id, dict):
            tenant_id = tenant_id.get("tenant_id") or tenant_id.get("tenantId") or ""

        if not tenant_id or not str(tenant_id).strip():
            raise ValueError("tenant_id is required")

        return self.service.activate(
            str(tenant_id).strip()
        )


    # =====================================================
    # Delete Tenant
    # =====================================================

    def delete(
        self,
        tenant_id: Any,
    ) -> bool:

        if isinstance(tenant_id, dict) or isinstance(tenant_id, str) and tenant_id.strip().startswith("{"):
            data = _extract_payload(tenant_id)
            tenant_id = data.get("tenant_id") or data.get("tenantId") or tenant_id

        if isinstance(tenant_id, dict):
            tenant_id = tenant_id.get("tenant_id") or tenant_id.get("tenantId") or ""

        if not tenant_id or not str(tenant_id).strip():
            raise ValueError("tenant_id is required")

        return self.service.remove(
            str(tenant_id).strip()
        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "api":
                "tenant_api",

            "status":
                "healthy",

        }
