from __future__ import annotations

from heshly_core.services.analytics.analytics_manager import (
    AnalyticsManager,
)


class AnalyticsService:
    """
    Analytics Service Layer.

    Application-facing service for analytics operations.

    Responsibilities:

        - Coordinate analytics workflows
        - Provide module-level analytics access
        - Aggregate analytics responses
        - Expose reporting operations

    Other Heshly modules should use this layer
    instead of directly accessing AnalyticsManager.
    """

    def __init__(self):

        self.manager = AnalyticsManager()


    # =====================================================
    # Overview
    # =====================================================

    def overview(self) -> dict:

        return self.manager.overview()


    # =====================================================
    # Metrics
    # =====================================================

    def metrics(self):

        return self.manager.metrics_list()


    # =====================================================
    # KPIs
    # =====================================================

    def kpis(self):

        return self.manager.kpis_list()


    # =====================================================
    # Dashboards
    # =====================================================

    def dashboards(self):

        return self.manager.dashboards()


    # =====================================================
    # Snapshots
    # =====================================================

    def snapshots(self):

        return self.manager.snapshots()


    # =====================================================
    # Reporting
    # =====================================================

    def report(
        self,
        report_type: str,
        filters: dict | None = None,
    ):

        return self.manager.report(
            report_type,
            filters,
        )


    # =====================================================
    # Trends
    # =====================================================

    def trends(
        self,
        metric: str,
        period: str = "monthly",
    ):

        return self.manager.trends(
            metric,
            period,
        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return self.manager.health()


    # =====================================================
    # Summary
    # =====================================================

    def summary(self):

        return {

            "overview": self.overview(),

            "metrics": len(
                self.metrics()
            ),

            "kpis": len(
                self.kpis()
            ),

            "dashboards": len(
                self.dashboards()
            ),

            "health": self.health(),

        }