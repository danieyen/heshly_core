from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any


# =====================================================
# Tenant Status
# =====================================================

class TenantStatus(str, Enum):

    ACTIVE = "active"

    TRIAL = "trial"

    SUSPENDED = "suspended"

    INACTIVE = "inactive"

    DELETED = "deleted"


# =====================================================
# Tenant Configuration
# =====================================================

@dataclass(slots=True)
class TenantConfiguration:

    timezone: str = "Africa/Nairobi"

    currency: str = "KES"

    language: str = "en"

    industry: str | None = None

    settings: dict[str, Any] = field(
        default_factory=dict
    )


# =====================================================
# Tenant Metadata
# =====================================================

@dataclass(slots=True)
class TenantMetadata:

    created_by: str | None = None

    source: str = "manual"

    tags: list[str] = field(
        default_factory=list
    )

    extra: dict[str, Any] = field(
        default_factory=dict
    )


# =====================================================
# Tenant
# =====================================================

@dataclass(slots=True)
class Tenant:

    tenant_id: str

    name: str

    status: TenantStatus = TenantStatus.TRIAL

    email: str | None = None

    phone: str | None = None

    configuration: TenantConfiguration = field(
        default_factory=TenantConfiguration
    )

    metadata: TenantMetadata = field(
        default_factory=TenantMetadata
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


    # =================================================
    # Lifecycle
    # =================================================

    def activate(self):

        self.status = TenantStatus.ACTIVE

        self.updated_at = datetime.now(UTC)



    def suspend(self):

        self.status = TenantStatus.SUSPENDED

        self.updated_at = datetime.now(UTC)



    def delete(self):

        self.status = TenantStatus.DELETED

        self.updated_at = datetime.now(UTC)



    # =================================================
    # Helpers
    # =================================================

    @property
    def is_active(self) -> bool:

        return self.status == TenantStatus.ACTIVE