from __future__ import annotations

from heshly_core.models.api_key import (
    APIKey,
)
from heshly_core.repositories.base_repository import (
    BaseRepository,
)


class APIKeyRepository(
    BaseRepository[APIKey]
):
    """
    In-memory repository for API keys.
    """

    def __init__(self):

        self._keys: dict[str, APIKey] = {}

    # =====================================================
    # CRUD
    # =====================================================

    def save(
        self,
        entity: APIKey,
    ) -> APIKey:

        self._keys[
            entity.key_id
        ] = entity

        return entity

    def get(
        self,
        entity_id: str,
    ) -> APIKey | None:

        return self._keys.get(
            entity_id
        )

    def list(
        self,
    ) -> list[APIKey]:

        return list(
            self._keys.values()
        )

    def delete(
        self,
        entity_id: str,
    ) -> bool:

        return (

            self._keys.pop(
                entity_id,
                None,
            )

            is not None

        )

    def exists(
        self,
        entity_id: str,
    ) -> bool:

        return (
            entity_id
            in self._keys
        )

    def count(
        self,
    ) -> int:

        return len(
            self._keys
        )

    def clear(
        self,
    ) -> None:

        self._keys.clear()

    # =====================================================
    # Queries
    # =====================================================

    def get_by_hash(
        self,
        key_hash: str,
    ) -> APIKey | None:

        for key in self._keys.values():

            if key.key_hash == key_hash:

                return key

        return None

    def list_by_tenant(
        self,
        tenant_id: str,
    ) -> list[APIKey]:

        return [

            key

            for key in self._keys.values()

            if key.tenant_id == tenant_id

        ]

    def list_active(
        self,
    ) -> list[APIKey]:

        return [

            key

            for key in self._keys.values()

            if key.is_active

        ]

    def list_expired(
        self,
    ) -> list[APIKey]:

        return [

            key

            for key in self._keys.values()

            if key.is_expired

        ]