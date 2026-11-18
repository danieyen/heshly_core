from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


# =====================================================
# Membership Roles
# =====================================================

class MembershipRole(str):

    OWNER = "owner"

    ADMINISTRATOR = "administrator"

    MANAGER = "manager"

    RECEPTIONIST = "receptionist"

    SALES = "sales"

    SUPPORT = "support"

    MARKETING = "marketing"

    ACCOUNTANT = "accountant"

    AI_MANAGER = "ai_manager"

    VIEWER = "viewer"


# =====================================================
# User Business Membership
# =====================================================

@dataclass(slots=True)
class UserBusinessMembership:

    membership_id: str

    user: str

    tenant_id: str

    business_id: str

    role: str = MembershipRole.VIEWER

    active: bool = True

    invited_by: str | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    # =================================================
    # Helpers
    # =================================================

    @property
    def is_owner(self) -> bool:

        return self.role == MembershipRole.OWNER


    @property
    def is_admin(self) -> bool:

        return self.role in (

            MembershipRole.OWNER,

            MembershipRole.ADMINISTRATOR,

        )


    @property
    def can_manage_users(self) -> bool:

        return self.role in (

            MembershipRole.OWNER,

            MembershipRole.ADMINISTRATOR,

            MembershipRole.MANAGER,

        )


    def deactivate(self):

        self.active = False


    def activate(self):

        self.active = True


    def change_role(
        self,
        role: str,
    ):

        self.role = role


    def summary(self):

        return {

            "membership_id": self.membership_id,

            "user": self.user,

            "tenant_id": self.tenant_id,

            "business_id": self.business_id,

            "role": self.role,

            "active": self.active,

        }
