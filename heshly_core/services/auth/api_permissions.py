from __future__ import annotations

from heshly_core.models.permissions import (
    UserPermissions,
)


class APIPermissions:
    """
    API permission checker.
    """


    def __init__(self):

        self.user_permissions = {}


    # =====================================================
    # Assign Permissions
    # =====================================================

    def assign(
        self,
        user_id: str,
        permissions: list[str],
    ):

        self.user_permissions[user_id] = (
            UserPermissions(

                user_id=user_id,

                permissions=permissions,

            )
        )


    # =====================================================
    # Check Permission
    # =====================================================

    def check(
        self,
        user_id: str,
        permission: str,
    ) -> bool:

        user = self.user_permissions.get(
            user_id
        )

        if user is None:

            return False


        return user.has_permission(
            permission
        )


    # =====================================================
    # Require Permission
    # =====================================================

    def require(
        self,
        user_id: str,
        permission: str,
    ):

        if not self.check(
            user_id,
            permission,
        ):

            raise PermissionError(
                f"Missing permission: {permission}"
            )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "api_permissions",

            "status":
                "healthy",

        }