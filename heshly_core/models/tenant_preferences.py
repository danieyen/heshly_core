from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class TenantPreferences:
    """
    Tenant Preferences.

    Stores tenant-specific user preferences.
    """

    tenant_id: str

    language: str = "en"

    timezone: str = "UTC"

    currency: str = "USD"

    date_format: str = "YYYY-MM-DD"

    time_format: str = "24h"

    theme: str = "light"

    notifications_enabled: bool = True

    dashboard: str = "default"

    ai_personality: str = "professional"

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def update(self, **kwargs):

        for key, value in kwargs.items():

            if hasattr(self, key):

                setattr(self, key, value)

        self.updated_at = datetime.now(UTC)