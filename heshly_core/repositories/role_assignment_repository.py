from __future__ import annotations

from heshly_core.models.role_assignment import (
    RoleAssignment,
)
from heshly_core.repositories.base_repository import (
    BaseRepository,
)


class RoleAssignmentRepository(
    BaseRepository[RoleAssignment]
):

    def __init__(self):

        self._assignments: dict[
            str,
            RoleAssignment,
        ] = {}


    def save(
        self,
        entity: RoleAssignment,
    ) -> RoleAssignment:

        self._assignments[
            entity.assignment_id
        ] = entity

        return entity


    def get(
        self,
        entity_id: str,
    ) -> RoleAssignment | None:

        return self._assignments.get(
            entity_id
        )


    def list(self):

        return list(
            self._assignments.values()
        )


    def delete(
        self,
        entity_id: str,
    ) -> bool:

        return (

            self._assignments.pop(
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
            in self._assignments
        )


    def count(self):

        return len(
            self._assignments
        )


    def clear(self):

        self._assignments.clear()


    # -----------------------------------------

    def list_by_user(
        self,
        user_id: str,
    ) -> list[RoleAssignment]:

        return [

            assignment

            for assignment in self.list()

            if assignment.user_id == user_id

        ]


    def list_by_role(
        self,
        role_id: str,
    ) -> list[RoleAssignment]:

        return [

            assignment

            for assignment in self.list()

            if assignment.role_id == role_id

        ]