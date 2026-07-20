from __future__ import annotations

from heshly_core.models.analytics import (
    AnalyticsSnapshot,
    Dashboard,
    KPI,
    Metric,
)

from heshly_core.repositories.analytics_repository import (
    AnalyticsRepository,
)

from heshly_core.services.analytics.metrics_engine import (
    MetricsEngine,
)

from heshly_core.services.analytics.kpi_calculator import (
    KPICalculator,
)

from heshly_core.services.analytics.time_series_aggregation import (
    TimeSeriesAggregation,
)

from heshly_core.services.analytics.data_filters import (
    DataFilters,
)


class AnalyticsManager:
    """
    Central Analytics Manager.

    Coordinates all analytics services and provides a single
    interface to the rest of Heshly.

    Components

        • Metrics Engine
        • KPI Calculator
        • Time Series Aggregation
        • Data Filters
        • Analytics Repository

    Future

        • ERPNext Integration
        • BI Engine
        • Reporting Engine
        • AI Analytics
        • Dashboard Engine
    """

    def __init__(self):

        self.repository = AnalyticsRepository()

        self.metrics = MetricsEngine()

        self.kpis = KPICalculator()

        self.time_series = TimeSeriesAggregation()

        self.filters = DataFilters()

    # =====================================================
    # Metrics
    # =====================================================

    def save_metric(
        self,
        metric: Metric,
    ) -> Metric:

        self.repository.save_metric(metric)

        return metric

    def metric(
        self,
        metric_id: str,
    ) -> Metric | None:

        return self.repository.get_metric(metric_id)

    def metrics_list(self) -> list[Metric]:

        return self.repository.all_metrics()

    # =====================================================
    # KPIs
    # =====================================================

    def save_kpi(
        self,
        kpi: KPI,
    ) -> KPI:

        self.repository.save_kpi(kpi)

        return kpi

    def kpi(
        self,
        kpi_id: str,
    ) -> KPI | None:

        return self.repository.get_kpi(kpi_id)

    def kpis_list(self) -> list[KPI]:

        return self.repository.all_kpis()

    # =====================================================
    # Dashboards
    # =====================================================

    def save_dashboard(
        self,
        dashboard: Dashboard,
    ) -> Dashboard:

        self.repository.save_dashboard(
            dashboard
        )

        return dashboard

    def dashboard(
        self,
        dashboard_id: str,
    ) -> Dashboard | None:

        return self.repository.get_dashboard(
            dashboard_id
        )

    def dashboards(
        self,
    ) -> list[Dashboard]:

        return self.repository.all_dashboards()

    # =====================================================
    # Snapshots
    # =====================================================

    def save_snapshot(
        self,
        snapshot: AnalyticsSnapshot,
    ) -> AnalyticsSnapshot:

        self.repository.save_snapshot(
            snapshot
        )

        return snapshot

    def snapshot(
        self,
        snapshot_id: str,
    ) -> AnalyticsSnapshot | None:

        return self.repository.get_snapshot(
            snapshot_id
        )

    def snapshots(
        self,
    ) -> list[AnalyticsSnapshot]:

        return self.repository.all_snapshots()


    # =====================================================
    # Overview Analytics
    # =====================================================

    def overview(self) -> dict:
        """
        Return high-level analytics overview.
        """

        return {

            "metrics": len(
                self.metrics_list()
            ),

            "kpis": len(
                self.kpis_list()
            ),

            "dashboards": len(
                self.dashboards()
            ),

            "snapshots": len(
                self.snapshots()
            ),

            "health": self.health(),

        }


    # =====================================================
    # Reports
    # =====================================================

    def report(
        self,
        report_type: str,
        filters: dict | None = None,
    ) -> dict:
        """
        Generate analytics report payload.
        """

        return {

            "type": report_type,

            "filters": filters or {},

            "overview": self.overview(),

            "metrics": self.metrics_list(),

            "kpis": self.kpis_list(),

        }


    # =====================================================
    # Trends
    # =====================================================

    def trends(
        self,
        metric: str,
        period: str = "monthly",
    ):

        return self.time_series.aggregate(
            metric,
            period,
        )    

    # =====================================================
    # Helpers
    # =====================================================

    def clear(self):

        self.repository.clear()

        self.metrics.clear()

        self.kpis.clear()

        self.time_series.clear()

    def health(self) -> dict:

        return {

            "repository": True,

            "metrics_engine": True,

            "kpi_calculator": True,

            "time_series": True,

            "data_filters": True,

        }

    def summary(self) -> dict:

        repository = self.repository.summary()

        metric_summary = self.metrics.summary()

        kpi_summary = self.kpis.summary()

        return {

            "repository": repository,

            "metrics": metric_summary,

            "kpis": kpi_summary,

            "health": self.health(),

        }