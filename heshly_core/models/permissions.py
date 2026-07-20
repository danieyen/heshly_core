from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Permission:

    name: str

    description: str | None = None



@dataclass(slots=True)
class UserPermissions:

    user_id: str

    permissions: list[str] = field(
        default_factory=list
    )


    def has_permission(
        self,
        permission: str,
    ) -> bool:

        return permission in self.permissions