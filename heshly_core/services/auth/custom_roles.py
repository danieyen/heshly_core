from __future__ import annotations

from copy import deepcopy

from heshly_core.models.role import (
    Permission,
    Role,
)
from heshly_core.repositories.role_repository import (
    RoleRepository,
)


class CustomRoles:
    """
    Manages tenant custom roles.
    """

    def __init__(
        self,
        repository: RoleRepository,
    ):

        self.repository = repository


    # =====================================================
    # Create
    # =====================================================

    def create(
        self,
        role: Role,
    ) -> Role:

        if role.system_role:

            raise ValueError(
                "Custom role cannot be a system role."
            )

        self.repository.save(role)

        return role


    # =====================================================
    # Copy Existing Role
    # =====================================================

    def copy(
        self,
        source_role: Role,
        role_id: str,
        name: str,
    ) -> Role:

        role = deepcopy(source_role)

        role.role_id = role_id

        role.name = name

        role.system_role = False

        self.repository.save(role)

        return role


    # =====================================================
    # Rename
    # =====================================================

    def rename(
        self,
        role_id: str,
        new_name: str,
    ) -> Role | None:

        role = self.repository.get(role_id)

        if role is None:

            return None

        role.name = new_name

        self.repository.save(role)

        return role


    # =====================================================
    # Permissions
    # =====================================================

    def add_permission(
        self,
        role_id: str,
        permission: Permission,
    ) -> bool:

        role = self.repository.get(role_id)

        if role is None:

            return False

        role.add_permission(permission)

        self.repository.save(role)

        return True


    def remove_permission(
        self,
        role_id: str,
        resource: str,
        action: str,
    ) -> bool:

        role = self.repository.get(role_id)

        if role is None:

            return False

        role.remove_permission(
            resource,
            action,
        )

        self.repository.save(role)

        return True


    # =====================================================
    # Delete
    # =====================================================

    def delete(
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

        return self.repository.delete(
            role_id
        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "custom_roles",

            "roles": self.repository.count(),

            "status": "healthy",

        }