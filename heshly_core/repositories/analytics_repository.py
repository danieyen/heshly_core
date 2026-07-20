from __future__ import annotations

from heshly_core.models.analytics import (
    AnalyticsSnapshot,
    Dashboard,
    KPI,
    Metric,
)


class AnalyticsRepository:
    """
    Analytics Repository

    In-memory repository for analytics data.

    Future implementation:
        - ERPNext DocTypes
        - MariaDB
        - PostgreSQL
        - External Data Warehouse
    """

    def __init__(self):

        self._metrics: dict[str, Metric] = {}

        self._kpis: dict[str, KPI] = {}

        self._dashboards: dict[str, Dashboard] = {}

        self._snapshots: dict[str, AnalyticsSnapshot] = {}

    # =====================================================
    # Metrics
    # =====================================================

    def save_metric(
        self,
        metric: Metric,
    ) -> Metric:

        self._metrics[
            metric.metric_id
        ] = metric

        return metric

    def get_metric(
        self,
        metric_id: str,
    ) -> Metric | None:

        return self._metrics.get(
            metric_id
        )

    def all_metrics(
        self,
    ) -> list[Metric]:

        return list(
            self._metrics.values()
        )

    def delete_metric(
        self,
        metric_id: str,
    ) -> bool:

        return (

            self._metrics.pop(
                metric_id,
                None,
            )
            is not None
        )

    # =====================================================
    # KPIs
    # =====================================================

    def save_kpi(
        self,
        kpi: KPI,
    ) -> KPI:

        self._kpis[
            kpi.kpi_id
        ] = kpi

        return kpi

    def get_kpi(
        self,
        kpi_id: str,
    ) -> KPI | None:

        return self._kpis.get(
            kpi_id
        )

    def all_kpis(
        self,
    ) -> list[KPI]:

        return list(
            self._kpis.values()
        )

    def delete_kpi(
        self,
        kpi_id: str,
    ) -> bool:

        return (

            self._kpis.pop(
                kpi_id,
                None,
            )
            is not None
        )

    # =====================================================
    # Dashboards
    # =====================================================

    def save_dashboard(
        self,
        dashboard: Dashboard,
    ) -> Dashboard:

        self._dashboards[
            dashboard.dashboard_id
        ] = dashboard

        return dashboard

    def get_dashboard(
        self,
        dashboard_id: str,
    ) -> Dashboard | None:

        return self._dashboards.get(
            dashboard_id
        )

    def all_dashboards(
        self,
    ) -> list[Dashboard]:

        return list(
            self._dashboards.values()
        )

    def delete_dashboard(
        self,
        dashboard_id: str,
    ) -> bool:

        return (

            self._dashboards.pop(
                dashboard_id,
                None,
            )
            is not None
        )

    # =====================================================
    # Snapshots
    # =====================================================

    def save_snapshot(
        self,
        snapshot: AnalyticsSnapshot,
    ) -> AnalyticsSnapshot:

        self._snapshots[
            snapshot.snapshot_id
        ] = snapshot

        return snapshot

    def get_snapshot(
        self,
        snapshot_id: str,
    ) -> AnalyticsSnapshot | None:

        return self._snapshots.get(
            snapshot_id
        )

    def all_snapshots(
        self,
    ) -> list[AnalyticsSnapshot]:

        return list(
            self._snapshots.values()
        )

    def delete_snapshot(
        self,
        snapshot_id: str,
    ) -> bool:

        return (

            self._snapshots.pop(
                snapshot_id,
                None,
            )
            is not None
        )

    # =====================================================
    # Utilities
    # =====================================================

    def clear(self):

        self._metrics.clear()

        self._kpis.clear()

        self._dashboards.clear()

        self._snapshots.clear()

    def summary(
        self,
    ) -> dict:

        return {

            "metrics": len(
                self._metrics
            ),

            "kpis": len(
                self._kpis
            ),

            "dashboards": len(
                self._dashboards
            ),

            "snapshots": len(
                self._snapshots
            ),

        }