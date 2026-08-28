from __future__ import annotations

from contextvars import ContextVar
from typing import Any


_current_tenant: ContextVar[str | None] = ContextVar(
    "current_tenant",
    default=None,
)


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


class TenantContext:
    """
    Stores the canonical tenant_id for the lifetime
    of the current request/execution context.
    Single source of truth for tenant isolation.
    Tolerant to n8n sending tenant_id nested under body/json or as JSON string.
    """

    def _extract_tenant_id(self, tenant_id: Any) -> str | None:
        if tenant_id is None:
            return None
        # Handle n8n wrapping
        if isinstance(tenant_id, dict):
            # Try to extract from nested structure
            for key in ("tenant_id", "tenantId", "tenant", "body", "json"):
                if key in tenant_id:
                    val = tenant_id[key]
                    if isinstance(val, str) and val.strip():
                        return val.strip()
                    if isinstance(val, dict):
                        # Recurse one level
                        for k2 in ("tenant_id", "tenantId"):
                            if k2 in val and isinstance(val[k2], str) and val[k2].strip():
                                return val[k2].strip()
            return None
        if isinstance(tenant_id, str):
            # Handle JSON string
            parsed = _parse_json_if_string(tenant_id)
            if isinstance(parsed, dict):
                return self._extract_tenant_id(parsed)
            return tenant_id.strip() if tenant_id.strip() else None
        return str(tenant_id).strip() if str(tenant_id).strip() else None

    def set(
        self,
        tenant_id: Any,
    ) -> None:

        extracted = self._extract_tenant_id(tenant_id)
        if not extracted:
            raise ValueError(
                "tenant_id is required and must be non-empty. Check phone_number_id -> tenant mapping and webhook tenant_id propagation. Ensure n8n Workflow Inputs include tenant_id and parent Execute Workflow maps it correctly."
            )

        _current_tenant.set(extracted)

    def get(
        self,
    ) -> str | None:

        return _current_tenant.get()

    def tenant_id(
        self,
    ) -> str | None:

        return self.get()

    def require(
        self,
    ) -> str:

        tenant_id = self.get()

        if tenant_id is None or not str(tenant_id).strip():
            raise RuntimeError(
                "No tenant context available. Tenant resolution failed - check phone_number_id -> tenant mapping and webhook tenant_id propagation. Ensure n8n parent workflow sets tenant_id via Workflow Inputs and child reads $json.tenant_id (not $json.body.tenant_id)."
            )

        return str(tenant_id).strip()

    def require_tenant(self) -> str:
        """Alias for require() for BaseRepository compatibility."""
        return self.require()

    def clear(
        self,
    ) -> None:

        _current_tenant.set(None)

    def has_context(
        self,
    ) -> bool:

        tenant = self.get()
        return tenant is not None and bool(str(tenant).strip())

    def set_from_payload(self, payload: Any) -> str:
        """
        Extract tenant_id from n8n payload that may be nested under body/json
        or be a JSON string. Sets context and returns tenant_id.
        """
        if isinstance(payload, dict) or isinstance(payload, str):
            data = _parse_json_if_string(payload)
            if isinstance(data, dict):
                # Try direct
                for key in ("tenant_id", "tenantId", "tenant"):
                    if key in data and isinstance(data[key], str) and data[key].strip():
                        self.set(data[key])
                        return self.require()
                # Try nested body/json
                for wrapper in ("body", "json", "data"):
                    if wrapper in data and isinstance(data[wrapper], dict):
                        for key in ("tenant_id", "tenantId"):
                            if key in data[wrapper] and isinstance(data[wrapper][key], str) and data[wrapper][key].strip():
                                self.set(data[wrapper][key])
                                return self.require()
        # Fallback to direct
        self.set(payload)
        return self.require()

    def health(
        self,
    ) -> dict:

        return {
            "service": "tenant_context",
            "status": "healthy",
            "tenant": self.get(),
            "has_context": self.has_context(),
        }
