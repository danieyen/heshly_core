from __future__ import annotations

from heshly_core.models.role import Role
from heshly_core.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """
    In-memory repository for roles.
    """

    def __init__(self):
        super().__init__()


        self._roles: dict[str, Role] = {}


    # =====================================================
    # CRUD
    # =====================================================

    def save(
        self,
        entity: Role,
    ) -> Role:

        self._roles[
            entity.role_id
        ] = entity

        return entity


    def get(
        self,
        entity_id: str,
    ) -> Role | None:

        return self._roles.get(
            entity_id
        )


    def list(self) -> list[Role]:

        return list(
            self._roles.values()
        )


    def delete(
        self,
        entity_id: str,
    ) -> bool:

        return (

            self._roles.pop(
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
            in
            self._roles
        )


    def count(self) -> int:

        return len(
            self._roles
        )


    def clear(self) -> None:

        self._roles.clear()


    # =====================================================
    # Role Queries
    # =====================================================

    def get_by_name(
        self,
        name: str,
    ) -> Role | None:

        for role in self._roles.values():

            if role.name == name:

                return role

        return None


    def list_by_type(
        self,
        role_type: str,
    ) -> list[Role]:

        return [

            role

            for role in self._roles.values()

            if role.role_type == role_type

        ]


    def health(self):

        return {

            "repository": "role_repository",

            "roles": self.count(),

            "status": "healthy",

        }