from __future__ import annotations

from heshly_core.models.role import Permission
from heshly_core.repositories.base_repository import BaseRepository


class PermissionRepository(BaseRepository[Permission]):
    """
    In-memory repository for permissions.
    """

    def __init__(self):
        super().__init__()


        self._permissions: dict[str, Permission] = {}


    # =====================================================
    # CRUD
    # =====================================================

    def save(
        self,
        entity: Permission,
    ) -> Permission:

        self._permissions[
            entity.permission_id
        ] = entity

        return entity


    def get(
        self,
        entity_id: str,
    ) -> Permission | None:

        return self._permissions.get(
            entity_id
        )


    def list(self) -> list[Permission]:

        return list(
            self._permissions.values()
        )


    def delete(
        self,
        entity_id: str,
    ) -> bool:

        return (

            self._permissions.pop(
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
            in self._permissions
        )


    def count(self) -> int:

        return len(
            self._permissions
        )


    def clear(self) -> None:

        self._permissions.clear()


    # =====================================================
    # Permission Queries
    # =====================================================

    def get_by_key(
        self,
        key: str,
    ) -> Permission | None:

        for permission in self._permissions.values():

            if permission.key == key:

                return permission

        return None


    def list_by_resource(
        self,
        resource: str,
    ) -> list[Permission]:

        return [

            permission

            for permission in self._permissions.values()

            if permission.resource == resource

        ]


    def list_by_category(
        self,
        category: str,
    ) -> list[Permission]:

        return [

            permission

            for permission in self._permissions.values()

            if permission.category == category

        ]


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "repository": "permission_repository",

            "permissions": self.count(),

            "status": "healthy",

        }