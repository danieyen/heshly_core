from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any



# =====================================================
# Team Member Status
# =====================================================

class TeamMemberStatus:

    ACTIVE = "active"

    INACTIVE = "inactive"

    ON_LEAVE = "on_leave"

    SUSPENDED = "suspended"



# =====================================================
# Team Member Types
# =====================================================

class TeamMemberType:

    EMPLOYEE = "employee"

    CONTRACTOR = "contractor"

    PARTNER = "partner"



# =====================================================
# Team Member Model
# =====================================================

@dataclass(slots=True)
class TeamMember:
    """
    Business team member.

    Represents a person working
    inside a business account.
    """


    member_id: str


    business_id: str


    user_id: str | None


    name: str


    job_title: str


    department: str | None = None


    member_type: str = TeamMemberType.EMPLOYEE


    status: str = TeamMemberStatus.ACTIVE



    email: str | None = None


    phone: str | None = None



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

        self.status = TeamMemberStatus.ACTIVE

        self.updated_at = datetime.now(UTC)



    def deactivate(self):

        self.status = TeamMemberStatus.INACTIVE

        self.updated_at = datetime.now(UTC)



    def suspend(self):

        self.status = TeamMemberStatus.SUSPENDED

        self.updated_at = datetime.now(UTC)



    def mark_leave(self):

        self.status = TeamMemberStatus.ON_LEAVE

        self.updated_at = datetime.now(UTC)



    # =================================================
    # Helpers
    # =================================================

    @property
    def is_active(self) -> bool:

        return (
            self.status
            ==
            TeamMemberStatus.ACTIVE
        )