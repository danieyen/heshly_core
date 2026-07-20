from __future__ import annotations

from heshly_core.models.dashboard import (
    Dashboard,
    DashboardSection,
    DashboardType,
)

from heshly_core.services.analytics.dashboard_widgets import (
    DashboardWidgets,
)


class KPIDashboard:
    """
    KPI Dashboard Builder.

    Builds the default KPI dashboard for a business.

    Displays

        • Revenue
        • Appointments
        • Customers
        • Leads
        • Opportunities
        • Conversion Rate
        • Win Rate
        • AI Accuracy
    """

    def __init__(self):

        self.widgets = DashboardWidgets()

    # =====================================================
    # Build Dashboard
    # =====================================================

    def build(
        self,
        metrics: dict | None = None,
    ) -> Dashboard:

        metrics = metrics or {}

        dashboard = Dashboard(

            dashboard_id="DASHBOARD-KPI",

            name="KPI Dashboard",

            dashboard_type=DashboardType.EXECUTIVE,

            description="Business KPI Dashboard",

        )

        # =================================================
        # Executive KPIs
        # =================================================

        executive = DashboardSection(

            section_id="SECTION-EXEC",

            title="Executive KPIs",

        )

        executive.add_widget(

            self.widgets.kpi(

                "Revenue",

                metrics.get(

                    "revenue",

                    0,

                ),

                "KES",

            )

        )

        executive.add_widget(

            self.widgets.kpi(

                "Appointments",

                metrics.get(

                    "appointments",

                    0,

                ),

            )

        )

        executive.add_widget(

            self.widgets.kpi(

                "Customers",

                metrics.get(

                    "customers",

                    0,

                ),

            )

        )

        executive.add_widget(

            self.widgets.kpi(

                "Leads",

                metrics.get(

                    "leads",

                    0,

                ),

            )

        )

        dashboard.add_section(

            executive

        )

        # =================================================
        # Sales
        # =================================================

        sales = DashboardSection(

            section_id="SECTION-SALES",

            title="Sales Performance",

        )

        sales.add_widget(

            self.widgets.progress(

                "Conversion Rate",

                metrics.get(

                    "conversion_rate",

                    0,

                ),

            )

        )

        sales.add_widget(

            self.widgets.progress(

                "Win Rate",

                metrics.get(

                    "win_rate",

                    0,

                ),

            )

        )

        sales.add_widget(

            self.widgets.number(

                "Open Opportunities",

                metrics.get(

                    "opportunities",

                    0,

                ),

            )

        )

        dashboard.add_section(

            sales

        )

        # =================================================
        # AI
        # =================================================

        ai = DashboardSection(

            section_id="SECTION-AI",

            title="AI Performance",

        )

        ai.add_widget(

            self.widgets.gauge(

                "AI Accuracy",

                metrics.get(

                    "ai_accuracy",

                    0,

                ),

            )

        )

        dashboard.add_section(

            ai

        )

        return dashboard

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        dashboard: Dashboard,
    ) -> dict:

        return {

            "dashboard": dashboard.name,

            "sections": dashboard.section_count,

            "widgets": dashboard.widget_count,

        }