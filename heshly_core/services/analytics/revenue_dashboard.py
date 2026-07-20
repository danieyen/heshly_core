from __future__ import annotations

from heshly_core.models.dashboard import (
    Dashboard,
    DashboardSection,
    DashboardType,
)

from heshly_core.services.analytics.dashboard_widgets import (
    DashboardWidgets,
)


class RevenueDashboard:
    """
    Revenue Dashboard Builder.

    Displays

        • Total Revenue
        • Monthly Revenue
        • Average Sale
        • Revenue Target
        • Revenue Trend
        • Revenue by Month
        • Revenue by Service
        • Revenue by Customer
    """

    def __init__(self):

        self.widgets = DashboardWidgets()

    # =====================================================
    # Dashboard Builder
    # =====================================================

    def build(
        self,
        revenue: dict | None = None,
    ) -> Dashboard:

        revenue = revenue or {}

        dashboard = Dashboard(

            dashboard_id="DASHBOARD-REVENUE",

            name="Revenue Dashboard",

            dashboard_type=DashboardType.SALES,

            description="Revenue analytics dashboard",

        )

        # =================================================
        # Revenue KPIs
        # =================================================

        overview = DashboardSection(

            section_id="SECTION-REVENUE-OVERVIEW",

            title="Revenue Overview",

        )

        overview.add_widget(

            self.widgets.kpi(

                "Total Revenue",

                revenue.get(

                    "total_revenue",

                    0,

                ),

                "KES",

            )

        )

        overview.add_widget(

            self.widgets.kpi(

                "Monthly Revenue",

                revenue.get(

                    "monthly_revenue",

                    0,

                ),

                "KES",

            )

        )

        overview.add_widget(

            self.widgets.kpi(

                "Average Sale",

                revenue.get(

                    "average_sale",

                    0,

                ),

                "KES",

            )

        )

        overview.add_widget(

            self.widgets.progress(

                "Revenue Target",

                revenue.get(

                    "target_percent",

                    0,

                ),

            )

        )

        dashboard.add_section(

            overview

        )

        # =================================================
        # Revenue Trends
        # =================================================

        trends = DashboardSection(

            section_id="SECTION-REVENUE-TRENDS",

            title="Revenue Trends",

        )

        trends.add_widget(

            self.widgets.line_chart(

                "Monthly Revenue",

                revenue.get(

                    "monthly_series",

                    [],

                ),

            )

        )

        dashboard.add_section(

            trends

        )

        # =================================================
        # Revenue Breakdown
        # =================================================

        breakdown = DashboardSection(

            section_id="SECTION-REVENUE-BREAKDOWN",

            title="Revenue Breakdown",

        )

        breakdown.add_widget(

            self.widgets.bar_chart(

                "Revenue by Service",

                revenue.get(

                    "service_breakdown",

                    [],

                ),

            )

        )

        breakdown.add_widget(

            self.widgets.pie_chart(

                "Revenue by Customer",

                revenue.get(

                    "customer_breakdown",

                    [],

                ),

            )

        )

        dashboard.add_section(

            breakdown

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