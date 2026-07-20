from __future__ import annotations

from heshly_core.services.calendar.calendar_manager import CalendarManager
from heshly_core.services.appointment_analytics.appointment_manager import (
    AppointmentAnalyticsManager,
)
from heshly_core.services.dashboard.dashboard_manager import (
    DashboardManager,
)


class CalendarAnalyticsIntegration:
    """
    Calendar Analytics Integration

    Connects the Calendar module with the
    Analytics subsystem.
    """

    def __init__(self):

        self.calendar = CalendarManager()

        self.analytics = AppointmentAnalyticsManager()

        self.dashboard = DashboardManager()

    # =====================================================
    # Calendar Snapshot
    # =====================================================

    def snapshot(self) -> dict:

        calendar_summary = {}

        if hasattr(self.calendar, "summary"):
            calendar_summary = self.calendar.summary()
        elif hasattr(self.calendar, "health"):
            calendar_summary = self.calendar.health()

        analytics_summary = {}

        if hasattr(self.analytics, "health"):
            analytics_summary = self.analytics.health()

        return {

            "calendar": calendar_summary,

            "appointment_analytics": analytics_summary,

        }

    # =====================================================
    # Dashboard Data
    # =====================================================

    def dashboard_data(self) -> dict:

        return {

            "calendar": self.snapshot(),

            "dashboard": (
                self.dashboard.health()
                if hasattr(self.dashboard, "health")
                else {}
            ),

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "calendar": (
                self.calendar.health()
                if hasattr(self.calendar, "health")
                else {"status": "unknown"}
            ),

            "appointment_analytics": (
                self.analytics.health()
                if hasattr(self.analytics, "health")
                else {"status": "unknown"}
            ),

            "dashboard": (
                self.dashboard.health()
                if hasattr(self.dashboard, "health")
                else {"status": "unknown"}
            ),

        }