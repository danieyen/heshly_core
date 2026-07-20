from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any


# =====================================================
# Business Account Status
# =====================================================

class BusinessAccountStatus(str):

    ACTIVE = "active"

    INACTIVE = "inactive"

    SUSPENDED = "suspended"



# =====================================================
# Business Profile
# =====================================================

@dataclass(slots=True)
class BusinessProfile:

    industry: str | None = None

    description: str | None = None

    website: str | None = None

    location: str | None = None

    address: str | None = None



# =====================================================
# Business Settings
# =====================================================

@dataclass(slots=True)
class BusinessSettings:

    timezone: str = "Africa/Nairobi"

    currency: str = "KES"

    language: str = "en"

    preferences: dict[str, Any] = field(
        default_factory=dict
    )



# =====================================================
# Business Account
# =====================================================

@dataclass(slots=True)
class BusinessAccount:

    business_id: str

    tenant_id: str

    name: str

    email: str | None = None

    phone: str | None = None

    status: str = BusinessAccountStatus.ACTIVE


    profile: BusinessProfile = field(
        default_factory=BusinessProfile
    )


    settings: BusinessSettings = field(
        default_factory=BusinessSettings
    )


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

        self.status = BusinessAccountStatus.ACTIVE

        self.updated_at = datetime.now(UTC)



    def suspend(self):

        self.status = BusinessAccountStatus.SUSPENDED

        self.updated_at = datetime.now(UTC)



    def deactivate(self):

        self.status = BusinessAccountStatus.INACTIVE

        self.updated_at = datetime.now(UTC)



    # =================================================
    # Helpers
    # =================================================

    @property
    def is_active(self) -> bool:

        return (
            self.status
            ==
            BusinessAccountStatus.ACTIVE
        )