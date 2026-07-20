from __future__ import annotations

from heshly_core.models.role import (
    Permission,
    PermissionAction,
    PermissionCategory,
    Role,
    RoleType,
)


class SystemRoles:
    """
    Factory for built-in system roles.
    """

    @staticmethod
    def platform_admin() -> Role:

        role = Role(

            role_id="system_platform_admin",

            name="Platform Admin",

            role_type=RoleType.ADMIN,

        )

        role.add_permission(
            Permission(
                permission_id="perm_admin_001",
                resource="system",
                action=PermissionAction.MANAGE,
                category=PermissionCategory.ADMIN,
                description="Full platform administration",
                system_permission=True,
            )
        )

        role.add_permission(
            Permission(
                permission_id="perm_admin_002",
                resource="tenant",
                action=PermissionAction.MANAGE,
                category=PermissionCategory.ADMIN,
                system_permission=True,
            )
        )

        return role


    @staticmethod
    def tenant_owner() -> Role:

        role = Role(

            role_id="system_tenant_owner",

            name="Tenant Owner",

            role_type=RoleType.OWNER,

        )

        permissions = [

            ("appointment", PermissionAction.MANAGE, PermissionCategory.APPOINTMENTS),

            ("crm", PermissionAction.MANAGE, PermissionCategory.CRM),

            ("calendar", PermissionAction.MANAGE, PermissionCategory.CALENDAR),

            ("ai", PermissionAction.MANAGE, PermissionCategory.AI),

            ("billing", PermissionAction.READ, PermissionCategory.BILLING),

            ("reports", PermissionAction.READ, PermissionCategory.REPORTS),

            ("users", PermissionAction.MANAGE, PermissionCategory.USERS),

            ("settings", PermissionAction.MANAGE, PermissionCategory.SETTINGS),

        ]

        for index, (resource, action, category) in enumerate(permissions, start=1):

            role.add_permission(

                Permission(

                    permission_id=f"owner_{index}",

                    resource=resource,

                    action=action,

                    category=category,

                    system_permission=True,

                )

            )

        return role


    @staticmethod
    def manager() -> Role:

        role = Role(

            role_id="system_manager",

            name="Manager",

            role_type=RoleType.MANAGER,

        )

        permissions = [

            ("appointment", PermissionAction.MANAGE, PermissionCategory.APPOINTMENTS),

            ("crm", PermissionAction.MANAGE, PermissionCategory.CRM),

            ("calendar", PermissionAction.READ, PermissionCategory.CALENDAR),

            ("reports", PermissionAction.READ, PermissionCategory.REPORTS),

        ]

        for index, (resource, action, category) in enumerate(permissions, start=1):

            role.add_permission(

                Permission(

                    permission_id=f"manager_{index}",

                    resource=resource,

                    action=action,

                    category=category,

                    system_permission=True,

                )

            )

        return role


    @staticmethod
    def staff() -> Role:

        role = Role(

            role_id="system_staff",

            name="Staff",

            role_type=RoleType.STAFF,

        )

        permissions = [

            ("appointment", PermissionAction.CREATE, PermissionCategory.APPOINTMENTS),

            ("appointment", PermissionAction.READ, PermissionCategory.APPOINTMENTS),

            ("calendar", PermissionAction.READ, PermissionCategory.CALENDAR),

        ]

        for index, (resource, action, category) in enumerate(permissions, start=1):

            role.add_permission(

                Permission(

                    permission_id=f"staff_{index}",

                    resource=resource,

                    action=action,

                    category=category,

                    system_permission=True,

                )

            )

        return role


    @staticmethod
    def receptionist() -> Role:

        role = Role(

            role_id="system_receptionist",

            name="Receptionist",

            role_type=RoleType.STAFF,

        )

        permissions = [

            ("appointment", PermissionAction.CREATE, PermissionCategory.APPOINTMENTS),

            ("appointment", PermissionAction.READ, PermissionCategory.APPOINTMENTS),

            ("crm", PermissionAction.READ, PermissionCategory.CRM),

        ]

        for index, (resource, action, category) in enumerate(permissions, start=1):

            role.add_permission(

                Permission(

                    permission_id=f"reception_{index}",

                    resource=resource,

                    action=action,

                    category=category,

                    system_permission=True,

                )

            )

        return role


    @staticmethod
    def viewer() -> Role:

        role = Role(

            role_id="system_viewer",

            name="Viewer",

            role_type=RoleType.STAFF,

        )

        permissions = [

            ("appointment", PermissionAction.READ, PermissionCategory.APPOINTMENTS),

            ("reports", PermissionAction.READ, PermissionCategory.REPORTS),

        ]

        for index, (resource, action, category) in enumerate(permissions, start=1):

            role.add_permission(

                Permission(

                    permission_id=f"viewer_{index}",

                    resource=resource,

                    action=action,

                    category=category,

                    system_permission=True,

                )

            )

        return role


    @staticmethod
    def all_roles() -> list[Role]:

        return [

            SystemRoles.platform_admin(),

            SystemRoles.tenant_owner(),

            SystemRoles.manager(),

            SystemRoles.staff(),

            SystemRoles.receptionist(),

            SystemRoles.viewer(),

        ]