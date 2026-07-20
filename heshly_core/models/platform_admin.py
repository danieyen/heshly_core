from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class PlatformAdminRole(str, Enum):
    """
    Platform administrator roles.
    """

    SUPER_ADMIN = "super_admin"

    SUPPORT = "support"

    SALES = "sales"

    BILLING = "billing"

    OPERATIONS = "operations"

    CUSTOMER_SUCCESS = "customer_success"


@dataclass(slots=True)
class PlatformAdmin:
    """
    Heshly Platform Administrator.

    Platform admins manage the SaaS
    platform itself, not tenant businesses.
    """

    admin_id: str

    first_name: str

    last_name: str

    email: str

    role: PlatformAdminRole

    active: bool = True

    verified: bool = False

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    last_login: datetime | None = None

    def activate(self):

        self.active = True

        self.updated_at = datetime.now(UTC)

    def suspend(self):

        self.active = False

        self.updated_at = datetime.now(UTC)

    def verify(self):

        self.verified = True

        self.updated_at = datetime.now(UTC)

    @property
    def full_name(self) -> str:

        return f"{self.first_name} {self.last_name}"