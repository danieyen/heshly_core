from __future__ import annotations

import uuid

from heshly_core.models.role_assignment import (
    RoleAssignment,
)
from heshly_core.repositories.role_assignment_repository import (
    RoleAssignmentRepository,
)


class RoleAssignmentManager:

    def __init__(
        self,
        repository: RoleAssignmentRepository,
    ):

        self.repository = repository


    def assign(

        self,

        user_id: str,

        role_id: str,

        tenant_id: str,

        assigned_by: str | None = None,

    ) -> RoleAssignment:

        assignment = RoleAssignment(

            assignment_id=str(
                uuid.uuid4()
            ),

            user_id=user_id,

            role_id=role_id,

            tenant_id=tenant_id,

            assigned_by=assigned_by,

        )

        return self.repository.save(
            assignment
        )


    def user_roles(
        self,
        user_id: str,
    ):

        return self.repository.list_by_user(
            user_id
        )


    def remove(
        self,
        assignment_id: str,
    ):

        return self.repository.delete(
            assignment_id
        )


    def health(self):

        return {

            "service": "role_assignment_manager",

            "assignments": self.repository.count(),

            "status": "healthy",

        }