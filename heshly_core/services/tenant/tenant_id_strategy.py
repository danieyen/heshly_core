from __future__ import annotations

import uuid


class TenantIDStrategy:
    """
    Tenant ID Strategy.

    Responsible for generating and validating
    tenant identifiers.

    Every tenant in Heshly must have a globally
    unique tenant_id.

    Future:

        • ERPNext Site IDs
        • UUID v7
        • Distributed ID generators
        • Human-readable aliases
    """

    PREFIX = "tenant"

    # =====================================================
    # Generation
    # =====================================================

    @classmethod
    def generate(cls) -> str:

        return f"{cls.PREFIX}_{uuid.uuid4().hex}"

    # =====================================================
    # Validation
    # =====================================================

    @classmethod
    def is_valid(
        cls,
        tenant_id: str,
    ) -> bool:

        if not tenant_id:

            return False

        return tenant_id.startswith(
            f"{cls.PREFIX}_"
        )

    # =====================================================
    # Helpers
    # =====================================================

    @classmethod
    def normalize(
        cls,
        tenant_id: str,
    ) -> str:

        return tenant_id.strip().lower()

    @classmethod
    def summary(cls) -> dict:

        return {

            "strategy": "uuid4",

            "prefix": cls.PREFIX,

        }

    @classmethod
    def health(cls) -> dict:

        return {

            "service": "tenant_id_strategy",

            "status": "healthy",

        }