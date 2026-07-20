from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4


# =====================================================
# Session Status
# =====================================================

class SessionStatus:

    ACTIVE = "active"

    EXPIRED = "expired"

    REVOKED = "revoked"


# =====================================================
# User Session
# =====================================================

@dataclass(slots=True)
class UserSession:
    """
    Represents an authenticated user session.
    """

    session_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    user_id: str = ""

    tenant_id: str | None = None

    access_token: str = ""

    refresh_token: str = ""

    ip_address: str = ""

    user_agent: str = ""

    status: str = SessionStatus.ACTIVE

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    last_activity: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    expires_at: datetime = field(
        default_factory=lambda: (
            datetime.now(UTC)
            + timedelta(hours=8)
        )
    )

    metadata: dict = field(
        default_factory=dict
    )

    # =====================================================
    # Properties
    # =====================================================

    @property
    def is_active(self) -> bool:

        return (
            self.status == SessionStatus.ACTIVE
            and
            not self.is_expired
        )

    @property
    def is_expired(self) -> bool:

        return datetime.now(UTC) >= self.expires_at

    @property
    def is_revoked(self) -> bool:

        return (
            self.status
            ==
            SessionStatus.REVOKED
        )

    # =====================================================
    # Operations
    # =====================================================

    def touch(self):

        self.last_activity = datetime.now(
            UTC
        )

    def extend(
        self,
        hours: int = 8,
    ):

        self.expires_at = (
            datetime.now(UTC)
            +
            timedelta(hours=hours)
        )

        self.touch()

    def expire(self):

        self.status = SessionStatus.EXPIRED

    def revoke(self):

        self.status = SessionStatus.REVOKED

    # =====================================================
    # Serialization
    # =====================================================

    def to_dict(self):

        return {

            "session_id": self.session_id,

            "user_id": self.user_id,

            "tenant_id": self.tenant_id,

            "access_token": self.access_token,

            "refresh_token": self.refresh_token,

            "ip_address": self.ip_address,

            "user_agent": self.user_agent,

            "status": self.status,

            "created_at": self.created_at,

            "last_activity": self.last_activity,

            "expires_at": self.expires_at,

            "metadata": self.metadata,

        }