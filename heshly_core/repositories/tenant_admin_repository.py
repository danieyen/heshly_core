from __future__ import annotations

from heshly_core.models.tenant import Tenant
from heshly_core.repositories.base_repository import (
    BaseRepository,
)


class TenantAdministrationRepository(
    BaseRepository[Tenant]
):
    """
    In-memory repository for tenant administration.
    """

    def __init__(self):

        self._storage: dict[str, Tenant] = {}

    def save(
        self,
        tenant: Tenant,
    ) -> Tenant:

        self._storage[
            tenant.tenant_id
        ] = tenant

        return tenant

    def get(
        self,
        entity_id: str,
    ) -> Tenant | None:

        return self._storage.get(
            entity_id
        )

    def list(self) -> list[Tenant]:

        return list(
            self._storage.values()
        )

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

    def exists(
        self,
        entity_id: str,
    ) -> bool:

        return entity_id in self._storage

    def count(self) -> int:

        return len(
            self._storage
        )

    def clear(self) -> None:

        self._storage.clear()