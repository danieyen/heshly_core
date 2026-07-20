from __future__ import annotations

from heshly_core.models.role import (
    Permission,
    Role,
)


class PermissionManager:
    """
    Permission Manager.

    Central service for evaluating
    role-based permissions.

    Future:
    - Tenant-aware permissions
    - Resource ownership
    - Field-level permissions
    - Feature flag enforcement
    """


    def has_permission(
        self,
        role: Role,
        resource: str,
        action: str,
    ) -> bool:
        """
        Check whether a role grants
        the requested permission.
        """

        return role.can(
            resource=resource,
            action=action,
        )


    def grant(
        self,
        role: Role,
        permission: Permission,
    ) -> None:
        """
        Add a permission to a role.
        """

        if not role.can(
            permission.resource,
            permission.action,
        ):
            role.add_permission(permission)


    def revoke(
        self,
        role: Role,
        resource: str,
        action: str,
    ) -> bool:
        """
        Remove a permission from a role.
        """

        original = len(role.permissions)

        role.permissions = [
            permission
            for permission in role.permissions
            if not (
                permission.resource == resource
                and permission.action == action
            )
        ]

        return len(role.permissions) != original


    def permissions(
        self,
        role: Role,
    ) -> list[Permission]:

        return list(role.permissions)


    def summary(
        self,
        role: Role,
    ) -> dict:

        return {
            "role": role.name,
            "permission_count": role.permission_count,
        }


    def health(self) -> dict:

        return {
            "service": "permission_manager",
            "status": "healthy",
        }