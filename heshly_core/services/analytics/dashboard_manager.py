from __future__ import annotations

from heshly_core.models.dashboard import (
    Dashboard,
)

from heshly_core.services.analytics.kpi_dashboard import (
    KPIDashboard,
)

from heshly_core.services.analytics.revenue_dashboard import (
    RevenueDashboard,
)

from heshly_core.services.analytics.appointment_dashboard import (
    AppointmentDashboard,
)

from heshly_core.services.analytics.crm_dashboard import (
    CRMDashboard,
)

from heshly_core.services.analytics.executive_dashboard import (
    ExecutiveDashboard,
)


class DashboardManager:
    """
    Dashboard Manager

    Central entry point for all dashboard generation.

    Managed Dashboards

        • KPI Dashboard
        • Revenue Dashboard
        • Appointment Dashboard
        • CRM Dashboard
        • Executive Dashboard

    Future

        • Marketing Dashboard
        • AI Dashboard
        • Operations Dashboard
        • Inventory Dashboard
        • Financial Dashboard
        • Custom Dashboard Builder
    """

    def __init__(self):

        self.kpi_dashboard = KPIDashboard()

        self.revenue_dashboard = RevenueDashboard()

        self.appointment_dashboard = AppointmentDashboard()

        self.crm_dashboard = CRMDashboard()

        self.executive_dashboard = ExecutiveDashboard()

        self._dashboards: dict[str, Dashboard] = {}

    # =====================================================
    # Dashboard Builders
    # =====================================================

    def build_kpi_dashboard(
        self,
        metrics: dict | None = None,
    ) -> Dashboard:

        dashboard = self.kpi_dashboard.build(metrics)

        self._dashboards[
            dashboard.dashboard_id
        ] = dashboard

        return dashboard

    def build_revenue_dashboard(
        self,
        revenue: dict | None = None,
    ) -> Dashboard:

        dashboard = self.revenue_dashboard.build(revenue)

        self._dashboards[
            dashboard.dashboard_id
        ] = dashboard

        return dashboard

    def build_appointment_dashboard(
        self,
        data: dict | None = None,
    ) -> Dashboard:

        dashboard = self.appointment_dashboard.build(data)

        self._dashboards[
            dashboard.dashboard_id
        ] = dashboard

        return dashboard

    def build_crm_dashboard(
        self,
        data: dict | None = None,
    ) -> Dashboard:

        dashboard = self.crm_dashboard.build(data)

        self._dashboards[
            dashboard.dashboard_id
        ] = dashboard

        return dashboard

    def build_executive_dashboard(
        self,
        data: dict | None = None,
    ) -> Dashboard:

        dashboard = self.executive_dashboard.build(data)

        self._dashboards[
            dashboard.dashboard_id
        ] = dashboard

        return dashboard

    # =====================================================
    # Dashboard Repository
    # =====================================================

    def get(
        self,
        dashboard_id: str,
    ) -> Dashboard | None:

        return self._dashboards.get(
            dashboard_id
        )

    def all(
        self,
    ) -> list[Dashboard]:

        return list(
            self._dashboards.values()
        )

    def delete(
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

    def exists(
        self,
        dashboard_id: str,
    ) -> bool:

        return dashboard_id in self._dashboards

    def clear(self):

        self._dashboards.clear()

    # =====================================================
    # Statistics
    # =====================================================

    def statistics(self) -> dict:

        by_type = {}

        total_sections = 0

        total_widgets = 0

        for dashboard in self._dashboards.values():

            dashboard_type = (
                dashboard.dashboard_type.value
            )

            by_type[
                dashboard_type
            ] = (

                by_type.get(
                    dashboard_type,
                    0,
                )
                + 1

            )

            total_sections += (
                dashboard.section_count
            )

            total_widgets += (
                dashboard.widget_count
            )

        return {

            "total_dashboards": len(
                self._dashboards
            ),

            "dashboard_types": by_type,

            "total_sections": total_sections,

            "total_widgets": total_widgets,

        }

    # =====================================================
    # Health Check
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "builders": {

                "kpi": True,

                "revenue": True,

                "appointment": True,

                "crm": True,

                "executive": True,

            },

            "stored_dashboards": len(
                self._dashboards
            ),

        }

    # =====================================================
    # Summary
    # =====================================================

    def summary(self) -> dict:

        return {

            **self.statistics(),

            "health": self.health(),

        }