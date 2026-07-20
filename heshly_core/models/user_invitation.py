from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class InvitationStatus(str, Enum):

    PENDING = "pending"

    ACCEPTED = "accepted"

    DECLINED = "declined"

    EXPIRED = "expired"


@dataclass(slots=True)
class UserInvitation:
    """
    Invitation to join a business.
    """

    invitation_id: str

    tenant_id: str

    business_id: str

    email: str

    role: str

    invited_by: str

    status: InvitationStatus = InvitationStatus.PENDING

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    accepted_at: datetime | None = None

    expires_at: datetime | None = None

    # =====================================================
    # Lifecycle
    # =====================================================

    def accept(self):

        self.status = InvitationStatus.ACCEPTED

        self.accepted_at = datetime.now(UTC)


    def decline(self):

        self.status = InvitationStatus.DECLINED


    def expire(self):

        self.status = InvitationStatus.EXPIRED


    @property
    def is_pending(self) -> bool:

        return self.status == InvitationStatus.PENDING