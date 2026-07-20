from __future__ import annotations

from heshly_core.models.auth import AuthUser
from heshly_core.models.role import (
    Permission,
    Role,
)
from heshly_core.repositories.permission_repository import (
    PermissionRepository,
)
from heshly_core.repositories.role_assignment_repository import (
    RoleAssignmentRepository,
)
from heshly_core.repositories.role_repository import (
    RoleRepository,
)
from heshly_core.services.auth.permission_inheritance import (
    PermissionInheritance,
)


class AuthorizationManager:
    """
    Handles authorization decisions.

    Uses role assignments together with
    permission inheritance to determine
    effective permissions.
    """

    def __init__(
        self,
        role_repository: RoleRepository,
        permission_repository: PermissionRepository,
        assignment_repository: RoleAssignmentRepository,
    ):

        self.role_repository = role_repository

        self.permission_repository = permission_repository

        self.assignment_repository = assignment_repository

        self.permission_inheritance = (
            PermissionInheritance(
                role_repository
            )
        )

    # =====================================================
    # Roles
    # =====================================================

    def get_roles(
        self,
        user_id: str,
    ) -> list[Role]:

        roles: list[Role] = []

        assignments = (
            self.assignment_repository.list_by_user(
                user_id
            )
        )

        for assignment in assignments:

            role = self.role_repository.get(
                assignment.role_id
            )

            if role is not None:

                roles.append(role)

        return roles

    # =====================================================
    # Role Inheritance
    # =====================================================

    def inherit_role(
        self,
        child_role_id: str,
        parent_role_id: str,
    ) -> None:

        self.permission_inheritance.inherit(
            child_role_id,
            parent_role_id,
        )

    # =====================================================
    # Effective Permissions
    # =====================================================

    def effective_permissions(
        self,
        user: AuthUser,
    ) -> list[Permission]:

        permissions: dict[str, Permission] = {}

        for role in self.get_roles(
            user.user_id
        ):

            for permission in (
                self.permission_inheritance.permissions(
                    role.role_id
                )
            ):

                permissions.setdefault(
                    permission.key,
                    permission,
                )

        return list(
            permissions.values()
        )

    # =====================================================
    # Authorization
    # =====================================================

    def has_permission(
        self,
        user: AuthUser,
        resource: str,
        action: str,
    ) -> bool:

        permission = (
            self.permission_repository.get_by_key(
                f"{resource}.{action}"
            )
        )

        if permission is None:

            return False

        if not permission.enabled:

            return False

        for effective in self.effective_permissions(
            user
        ):

            if (
                effective.resource == resource
                and
                effective.action == action
                and
                effective.enabled
            ):

                return True

        return False

    # =====================================================
    # Permissions
    # =====================================================

    def list_permissions(
        self,
        user: AuthUser,
    ) -> list[Permission]:

        return self.effective_permissions(
            user
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "authorization_manager",

            "roles": self.role_repository.count(),

            "permissions": self.permission_repository.count(),

            "assignments": self.assignment_repository.count(),

            "inheritance_links": len(
                self.permission_inheritance._parents
            ),

            "status": "healthy",

        }