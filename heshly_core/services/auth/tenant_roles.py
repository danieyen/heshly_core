from __future__ import annotations

from copy import deepcopy

from heshly_core.models.role import (
    Role,
)
from heshly_core.repositories.role_repository import (
    RoleRepository,
)


class TenantRoles:
    """
    Manages tenant-specific roles.
    """

    def __init__(
        self,
        repository: RoleRepository,
    ):

        self.repository = repository


    # =====================================================
    # Create
    # =====================================================

    def create_role(
        self,
        tenant_id: str,
        role: Role,
    ) -> Role:

        role.tenant_id = tenant_id

        self.repository.save(role)

        return role


    # =====================================================
    # Clone System Role
    # =====================================================

    def clone_system_role(
        self,
        tenant_id: str,
        system_role: Role,
        role_id: str,
        name: str,
    ) -> Role:

        role = deepcopy(system_role)

        role.role_id = role_id

        role.name = name

        role.tenant_id = tenant_id

        role.system_role = False

        self.repository.save(role)

        return role


    # =====================================================
    # Get
    # =====================================================

    def get_role(
        self,
        role_id: str,
    ) -> Role | None:

        return self.repository.get(role_id)


    # =====================================================
    # List
    # =====================================================

    def list_roles(
        self,
        tenant_id: str,
    ) -> list[Role]:

        return [

            role

            for role in self.repository.list()

            if role.tenant_id == tenant_id

        ]


    # =====================================================
    # Delete
    # =====================================================

    def delete_role(
        self,
        role_id: str,
    ) -> bool:

        role = self.repository.get(role_id)

        if role is None:

            return False

        if role.system_role:

            raise ValueError(
                "System roles cannot be deleted."
            )

        return self.repository.delete(role_id)


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "tenant_roles",

            "roles": self.repository.count(),

            "status": "healthy",

        }