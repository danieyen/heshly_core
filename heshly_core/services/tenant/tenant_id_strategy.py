from __future__ import annotations

import re


class TenantIDStrategy:
    """
    Canonical tenant ID generation.
    """

    @classmethod
    def from_business_id(
        cls,
        business_id: str,
    ) -> str:

        tenant = business_id.strip().lower()

        tenant = re.sub(
            r"[^a-z0-9]+",
            "_",
            tenant,
        )

        return tenant.strip("_")

    @classmethod
    def generate(
        cls,
        business_id: str,
    ) -> str:

        return cls.from_business_id(
            business_id,
        )

    @classmethod
    def normalize(
        cls,
        tenant_id: str,
    ) -> str:

        return cls.from_business_id(
            tenant_id,
        )

    @classmethod
    def is_valid(
        cls,
        tenant_id: str,
    ) -> bool:

        return bool(
            cls.normalize(tenant_id)
        )

    @classmethod
    def health(cls):

        return {
            "service": "tenant_id_strategy",
            "status": "healthy",
        }
