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
    """

    def set(
        self,
        tenant_id: str,
    ) -> None:

        if not tenant_id:
            raise ValueError(
                "tenant_id is required."
            )

        _current_tenant.set(
            tenant_id
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

        if tenant_id is None:
            raise RuntimeError(
                "No tenant context available."
            )

        return tenant_id

    def clear(
        self,
    ) -> None:

        _current_tenant.set(None)

    def has_context(
        self,
    ) -> bool:

        return self.get() is not None

    def health(
        self,
    ) -> dict:

        return {
            "service": "tenant_context",
            "status": "healthy",
            "tenant": self.get(),
            "has_context": self.has_context(),
        }
