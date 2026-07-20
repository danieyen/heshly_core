from __future__ import annotations

from heshly_core.models.role import (
    Permission,
    Role,
)
from heshly_core.repositories.role_repository import (
    RoleRepository,
)


class PermissionInheritance:
    """
    Resolves inherited permissions
    between roles.
    """

    def __init__(
        self,
        role_repository: RoleRepository,
    ):

        self.role_repository = role_repository

        self._parents: dict[str, str] = {}

    # =====================================================
    # Inheritance
    # =====================================================

    def inherit(
        self,
        child_role_id: str,
        parent_role_id: str,
    ) -> None:

        if child_role_id == parent_role_id:

            raise ValueError(
                "A role cannot inherit from itself."
            )

        self._parents[
            child_role_id
        ] = parent_role_id

    # =====================================================
    # Parent
    # =====================================================

    def parent(
        self,
        role_id: str,
    ) -> Role | None:

        parent_id = self._parents.get(
            role_id
        )

        if parent_id is None:

            return None

        return self.role_repository.get(
            parent_id
        )

    # =====================================================
    # Effective Permissions
    # =====================================================

    def permissions(
        self,
        role_id: str,
    ) -> list[Permission]:

        visited: set[str] = set()

        permissions: dict[str, Permission] = {}

        current = self.role_repository.get(
            role_id
        )

        while current is not None:

            if current.role_id in visited:

                raise ValueError(
                    "Circular role inheritance detected."
                )

            visited.add(
                current.role_id
            )

            for permission in current.permissions:

                permissions.setdefault(
                    permission.key,
                    permission,
                )

            parent = self.parent(
                current.role_id
            )

            current = parent

        return list(
            permissions.values()
        )

    # =====================================================
    # Effective Access
    # =====================================================

    def has_permission(
        self,
        role_id: str,
        resource: str,
        action: str,
    ) -> bool:

        for permission in self.permissions(
            role_id
        ):

            if (

                permission.resource == resource

                and

                permission.action == action

                and

                permission.enabled

            ):

                return True

        return False

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "permission_inheritance",

            "roles": self.role_repository.count(),

            "inheritance_links": len(
                self._parents
            ),

            "status": "healthy",

        }