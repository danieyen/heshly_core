from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


# =====================================================
# User Status
# =====================================================

class UserStatus(str, Enum):

    ACTIVE = "active"

    INVITED = "invited"

    DISABLED = "disabled"

    LOCKED = "locked"


# =====================================================
# User Role
# =====================================================

class UserRole(str, Enum):

    PLATFORM_ADMIN = "platform_admin"

    TENANT_OWNER = "tenant_owner"

    MANAGER = "manager"

    STAFF = "staff"


# =====================================================
# Authentication User
# =====================================================

@dataclass(slots=True)
class AuthUser:
    """
    Authenticated user.
    """

    user_id: str

    email: str

    tenant_id: str | None = None

    password_hash: str = ""

    first_name: str = ""

    last_name: str = ""

    role: UserRole = UserRole.STAFF

    status: UserStatus = UserStatus.ACTIVE

    authenticated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    last_login: datetime | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    @property
    def full_name(self) -> str:

        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_active(self) -> bool:

        return self.status == UserStatus.ACTIVE

    def activate(self):

        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.now(UTC)

    def disable(self):

        self.status = UserStatus.DISABLED
        self.updated_at = datetime.now(UTC)

    def lock(self):

        self.status = UserStatus.LOCKED
        self.updated_at = datetime.now(UTC)

    def record_login(self):

        self.last_login = datetime.now(UTC)
        self.updated_at = self.last_login

    def health(self):

        return {

            "model": "auth_user",

            "status": "healthy",

        }