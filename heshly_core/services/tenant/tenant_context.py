from __future__ import annotations

from contextvars import ContextVar


_current_tenant: ContextVar[str | None] = ContextVar(
    "current_tenant",
    default=None,
)


class TenantContext:
    """
    Stores the canonical tenant_id for the lifetime
    of the current request/execution context.
    Single source of truth for tenant isolation.
    """

    def set(
        self,
        tenant_id: str,
    ) -> None:

        if not tenant_id or not str(tenant_id).strip():
            raise ValueError(
                "tenant_id is required and must be non-empty."
            )

        _current_tenant.set(
            str(tenant_id).strip()
        )

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
                "No tenant context available. Tenant resolution failed - check phone_number_id -> tenant mapping and webhook tenant_id propagation."
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

    def health(
        self,
    ) -> dict:

        return {
            "service": "tenant_context",
            "status": "healthy",
            "tenant": self.get(),
            "has_context": self.has_context(),
        }
