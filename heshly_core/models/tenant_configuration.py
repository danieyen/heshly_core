from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


# =====================================================
# Configuration Scope
# =====================================================

class ConfigurationScope(str, Enum):

    SYSTEM = "system"

    TENANT = "tenant"

    BUSINESS = "business"

    USER = "user"


# =====================================================
# Configuration Entry
# =====================================================

@dataclass(slots=True)
class ConfigurationEntry:

    key: str

    value: Any

    description: str = ""

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


# =====================================================
# Tenant Configuration
# =====================================================

@dataclass(slots=True)
class TenantConfiguration:
    """
    Root configuration for a tenant.
    """

    tenant_id: str

    scope: ConfigurationScope = (
        ConfigurationScope.TENANT
    )

    settings: dict[str, ConfigurationEntry] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    # =================================================
    # Configuration Management
    # =================================================

    def set(
        self,
        key: str,
        value: Any,
        description: str = "",
    ):

        self.settings[key] = ConfigurationEntry(

            key=key,

            value=value,

            description=description,

        )

        self.updated_at = datetime.now(UTC)

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        entry = self.settings.get(key)

        if entry is None:

            return default

        return entry.value

    def remove(
        self,
        key: str,
    ) -> bool:

        if key not in self.settings:

            return False

        del self.settings[key]

        self.updated_at = datetime.now(UTC)

        return True

    def exists(
        self,
        key: str,
    ) -> bool:

        return key in self.settings

    @property
    def count(self) -> int:

        return len(self.settings)