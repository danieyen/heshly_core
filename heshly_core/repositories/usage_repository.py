from __future__ import annotations

from heshly_core.models.usage import (
    TenantUsage,
)

from heshly_core.repositories.base_repository import (
    BaseRepository,
)


class UsageRepository(
    BaseRepository[TenantUsage]
):
    """
    Repository for tenant usage records.

    Stores usage events and metrics.
    """

    def __init__(self):

        self._storage: dict[
            str,
            TenantUsage,
        ] = {}


    # =====================================================
    # Save
    # =====================================================

    def save(
        self,
        entity: TenantUsage,
    ) -> TenantUsage:

        self._storage[
            entity.usage_id
        ] = entity

        return entity


    # =====================================================
    # Get
    # =====================================================

    def get(
        self,
        entity_id: str,
    ) -> TenantUsage | None:

        return self._storage.get(
            entity_id
        )


    # =====================================================
    # List
    # =====================================================

    def list(self) -> list[TenantUsage]:

        return list(
            self._storage.values()
        )


    # =====================================================
    # Tenant Usage
    # =====================================================

    def list_by_tenant(
        self,
        tenant_id: str,
    ) -> list[TenantUsage]:

        return [

            usage

            for usage in self._storage.values()

            if usage.tenant_id == tenant_id

        ]


    # =====================================================
    # Metric Filtering
    # =====================================================

    def list_by_metric(
        self,
        metric,
    ) -> list[TenantUsage]:

        return [

            usage

            for usage in self._storage.values()

            if usage.metric == metric

        ]


    # =====================================================
    # Delete
    # =====================================================

    def delete(
        self,
        entity_id: str,
    ) -> bool:

        return (

            self._storage.pop(
                entity_id,
                None,
            )

            is not None

        )


    # =====================================================
    # Exists
    # =====================================================

    def exists(
        self,
        entity_id: str,
    ) -> bool:

        return entity_id in self._storage


    # =====================================================
    # Count
    # =====================================================

    def count(self) -> int:

        return len(
            self._storage
        )


    # =====================================================
    # Clear
    # =====================================================

    def clear(self):

        self._storage.clear()


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "repository":
                "usage_repository",

            "records":
                self.count(),

            "status":
                "healthy",

        }