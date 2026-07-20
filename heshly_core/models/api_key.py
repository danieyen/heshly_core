from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


# =====================================================
# API Key Status
# =====================================================

class APIKeyStatus(str, Enum):

    ACTIVE = "active"

    DISABLED = "disabled"

    REVOKED = "revoked"

    EXPIRED = "expired"


# =====================================================
# API Key Scope
# =====================================================

class APIKeyScope(str, Enum):

    FULL = "full"

    READ_ONLY = "read_only"

    CRM = "crm"

    CALENDAR = "calendar"

    AI = "ai"

    ANALYTICS = "analytics"

    ADMIN = "admin"


# =====================================================
# API Key
# =====================================================

@dataclass(slots=True)
class APIKey:
    """
    Represents an API key used to
    authenticate external systems.
    """

    key_id: str

    tenant_id: str

    name: str

    key_hash: str

    scope: APIKeyScope = APIKeyScope.FULL

    status: APIKeyStatus = APIKeyStatus.ACTIVE

    created_by: str | None = None

    last_used_at: datetime | None = None

    expires_at: datetime | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    # =================================================
    # Lifecycle
    # =================================================

    def disable(self):

        self.status = APIKeyStatus.DISABLED

        self.updated_at = datetime.now(UTC)


    def enable(self):

        self.status = APIKeyStatus.ACTIVE

        self.updated_at = datetime.now(UTC)


    def revoke(self):

        self.status = APIKeyStatus.REVOKED

        self.updated_at = datetime.now(UTC)


    def expire(self):

        self.status = APIKeyStatus.EXPIRED

        self.updated_at = datetime.now(UTC)


    def mark_used(self):

        self.last_used_at = datetime.now(UTC)


    # =================================================
    # Properties
    # =================================================

    @property
    def is_active(self) -> bool:

        return self.status == APIKeyStatus.ACTIVE

    @property
    def is_expired(self) -> bool:

        if self.expires_at is None:

            return False

        return datetime.now(UTC) >= self.expires_at