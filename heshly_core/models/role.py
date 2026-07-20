from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC



# =====================================================
# Permission Categories
# =====================================================

class PermissionCategory:

    APPOINTMENTS = "appointments"

    CRM = "crm"

    CALENDAR = "calendar"

    AI = "ai"

    USERS = "users"

    BILLING = "billing"

    REPORTS = "reports"

    SETTINGS = "settings"

    ADMIN = "admin"

# =====================================================
# Permission Actions
# =====================================================

class PermissionAction:

    CREATE = "create"

    READ = "read"

    UPDATE = "update"

    DELETE = "delete"

    MANAGE = "manage"



# =====================================================
# Role Types
# =====================================================

class RoleType:

    OWNER = "owner"

    ADMIN = "admin"

    MANAGER = "manager"

    STAFF = "staff"

    CUSTOM = "custom"



# =====================================================
# Permission Model
# =====================================================

@dataclass(slots=True)
class Permission:
    """
    Individual system permission.
    """

    permission_id: str

    resource: str

    action: str

    tenant_id: str | None = None

    system_role: bool = False

    category: str = PermissionCategory.ADMIN

    description: str = ""

    enabled: bool = True

    system_permission: bool = False

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    @property
    def key(self) -> str:

        return f"{self.resource}.{self.action}"


    def disable(self):

        self.enabled = False


    def enable(self):

        self.enabled = True


    @property
    def is_enabled(self):

        return self.enabled


    def health(self):

        return {

            "model": "permission",

            "key": self.key,

            "enabled": self.enabled,

            "status": "healthy",

        }

# =====================================================
# Role Model
# =====================================================

@dataclass(slots=True)
class Role:

    role_id: str

    name: str

    role_type: str = RoleType.CUSTOM

    tenant_id: str | None = None

    system_role: bool = False

    description: str = ""

    permissions: list[Permission] = field(
        default_factory=list
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


    # =================================================
    # Permissions
    # =================================================

    def add_permission(
        self,
        permission: Permission,
    ):

        self.permissions.append(
            permission
        )



    def can(
        self,
        resource: str,
        action: str,
    ) -> bool:


        for permission in self.permissions:

            if (
                permission.resource == resource
                    and
                permission.action == action
                and
                permission.enabled
            ):

                return True


        return False



    @property
    def permission_count(self):

        return len(
            self.permissions
        )

    def remove_permission(
        self,
        resource: str,
        action: str,
    ):

        self.permissions = [

            permission

            for permission in self.permissions

            if not (

                permission.resource == resource

                and

                permission.action == action

            )

        ]


    def has_permission(
        self,
        permission_key: str,
    ) -> bool:

        return any(

            permission.key == permission_key

            for permission in self.permissions

        )


    def health(self):

        return {

            "model": "role",

            "permissions": self.permission_count,

            "status": "healthy",

        }    