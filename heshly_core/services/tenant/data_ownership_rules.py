from __future__ import annotations


class DataOwnershipRules:
    """
    Data Ownership Rules.

    Central ownership validation service
    for multi-tenant resources.
    """

    # =====================================================
    # Validation
    # =====================================================

    @staticmethod
    def belongs_to_tenant(
        resource,
        tenant_id: str,
    ) -> bool:

        return getattr(
            resource,
            "tenant_id",
            None,
        ) == tenant_id

    @staticmethod
    def require_owner(
        resource,
        tenant_id: str,
    ) -> None:

        if not DataOwnershipRules.belongs_to_tenant(
            resource,
            tenant_id,
        ):

            raise PermissionError(
                "Resource does not belong to the current tenant."
            )

    # =====================================================
    # Ownership
    # =====================================================

    @staticmethod
    def assign_owner(
        resource,
        tenant_id: str,
    ):

        setattr(
            resource,
            "tenant_id",
            tenant_id,
        )

        return resource

    @staticmethod
    def transfer_owner(
        resource,
        new_tenant_id: str,
    ):

        setattr(
            resource,
            "tenant_id",
            new_tenant_id,
        )

        return resource

    # =====================================================
    # Helpers
    # =====================================================

    @staticmethod
    def owner(resource) -> str | None:

        return getattr(
            resource,
            "tenant_id",
            None,
        )

    @staticmethod
    def summary() -> dict:

        return {

            "ownership_model": "tenant_based",

            "cross_tenant_access": False,

        }

    @staticmethod
    def health() -> dict:

        return {

            "service": "data_ownership_rules",

            "status": "healthy",

        }