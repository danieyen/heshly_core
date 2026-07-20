from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any


# =====================================================
# Notification Settings
# =====================================================

@dataclass(slots=True)
class NotificationSettings:

    whatsapp_enabled: bool = True

    email_enabled: bool = True

    sms_enabled: bool = False

    reminders_enabled: bool = True



# =====================================================
# AI Settings
# =====================================================

@dataclass(slots=True)
class AISettings:

    enabled: bool = True

    personality: str = "professional"

    response_language: str = "en"

    human_handover_enabled: bool = True



# =====================================================
# Integration Settings
# =====================================================

@dataclass(slots=True)
class IntegrationSettings:

    calendar_enabled: bool = True

    payments_enabled: bool = False

    crm_enabled: bool = True

    analytics_enabled: bool = True



# =====================================================
# Business Settings
# =====================================================

@dataclass(slots=True)
class BusinessSettings:
    """
    Operational configuration for a business.
    """


    business_id: str


    timezone: str = "Africa/Nairobi"

    currency: str = "KES"

    language: str = "en"


    business_hours: dict[str, Any] = field(
        default_factory=dict
    )


    notifications: NotificationSettings = field(
        default_factory=NotificationSettings
    )


    ai: AISettings = field(
        default_factory=AISettings
    )


    integrations: IntegrationSettings = field(
        default_factory=IntegrationSettings
    )


    metadata: dict[str, Any] = field(
        default_factory=dict
    )


    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


    # =================================================
    # Updates
    # =================================================

    def update_timezone(
        self,
        timezone: str,
    ):

        self.timezone = timezone

        self.updated_at = datetime.now(UTC)



    def update_currency(
        self,
        currency: str,
    ):

        self.currency = currency

        self.updated_at = datetime.now(UTC)



    def update_language(
        self,
        language: str,
    ):

        self.language = language

        self.updated_at = datetime.now(UTC)



    # =================================================
    # Summary
    # =================================================

    def summary(self) -> dict:

        return {

            "business_id": self.business_id,

            "timezone": self.timezone,

            "currency": self.currency,

            "language": self.language,

            "ai_enabled": self.ai.enabled,

            "calendar_enabled":
                self.integrations.calendar_enabled,

        }