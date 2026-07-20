from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any


# =====================================================
# User Status
# =====================================================

class UserStatus:

    ACTIVE = "active"

    INACTIVE = "inactive"

    SUSPENDED = "suspended"



# =====================================================
# User Role
# =====================================================

class UserRole:

    OWNER = "owner"

    ADMIN = "admin"

    MANAGER = "manager"

    STAFF = "staff"

    VIEWER = "viewer"



# =====================================================
# User Model
# =====================================================

@dataclass(slots=True)
class User:
    """
    Heshly user account.

    Represents a person accessing
    a tenant/business account.
    """


    user_id: str


    tenant_id: str


    name: str


    email: str


    phone: str | None = None


    role: str = UserRole.STAFF


    status: str = UserStatus.ACTIVE



    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )



    metadata: dict[str, Any] = field(
        default_factory=dict
    )



    # =================================================
    # Lifecycle
    # =================================================

    def activate(self):

        self.status = UserStatus.ACTIVE

        self.updated_at = datetime.now(UTC)



    def deactivate(self):

        self.status = UserStatus.INACTIVE

        self.updated_at = datetime.now(UTC)



    def suspend(self):

        self.status = UserStatus.SUSPENDED

        self.updated_at = datetime.now(UTC)



    # =================================================
    # Helpers
    # =================================================

    @property
    def is_active(self) -> bool:

        return (
            self.status
            ==
            UserStatus.ACTIVE
        )



    def has_role(
        self,
        role: str,
    ) -> bool:

        return self.role == role