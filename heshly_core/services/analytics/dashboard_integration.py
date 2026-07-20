from __future__ import annotations

from heshly_core.services.dashboard.dashboard_manager import (
    DashboardManager,
)
from heshly_core.services.analytics.analytics_manager import (
    AnalyticsManager,
)
from heshly_core.services.business_intelligence.bi_manager import (
    BIManager,
)
from heshly_core.services.reporting.report_manager import (
    ReportManager,
)


class DashboardIntegration:
    """
    Dashboard Integration

    Central integration layer between dashboards,
    analytics, reporting and business intelligence.
    """

    def __init__(self):

        self.dashboard = DashboardManager()

        self.analytics = AnalyticsManager()

        self.business_intelligence = BIManager()

        self.reporting = ReportManager()

    # =====================================================
    # Dashboard Snapshot
    # =====================================================

    def snapshot(self) -> dict:

        snapshot = {}

        if hasattr(self.dashboard, "summary"):
            snapshot["dashboard"] = (
                self.dashboard.summary()
            )
        elif hasattr(self.dashboard, "health"):
            snapshot["dashboard"] = (
                self.dashboard.health()
            )

        if hasattr(self.analytics, "health"):
            snapshot["analytics"] = (
                self.analytics.health()
            )

        if hasattr(
            self.business_intelligence,
            "health",
        ):
            snapshot["business_intelligence"] = (
                self.business_intelligence.health()
            )

        if hasattr(self.reporting, "health"):
            snapshot["reporting"] = (
                self.reporting.health()
            )

        return snapshot

    # =====================================================
    # Executive Dashboard
    # =====================================================

    def executive_dashboard(self) -> dict:

        return {

            "module": "Executive Dashboard",

            "snapshot": self.snapshot(),

        }

    # =====================================================
    # KPI Dashboard
    # =====================================================

    def kpi_dashboard(self) -> dict:

        return {

            "dashboard": (
                self.dashboard.health()
                if hasattr(
                    self.dashboard,
                    "health",
                )
                else {}
            ),

            "analytics": (
                self.analytics.health()
            ),

        }

    # =====================================================
    # Reporting Dashboard
    # =====================================================

    def reporting_dashboard(self) -> dict:

        return {

            "reporting": (
                self.reporting.health()
            ),

            "business_intelligence": (
                self.business_intelligence.health()
            ),

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "services": {

                "dashboard": (
                    self.dashboard.health()
                    if hasattr(
                        self.dashboard,
                        "health",
                    )
                    else {"status": "unknown"}
                ),

                "analytics": (
                    self.analytics.health()
                ),

                "business_intelligence": (
                    self.business_intelligence.health()
                ),

                "reporting": (
                    self.reporting.health()
                ),

            },

        }