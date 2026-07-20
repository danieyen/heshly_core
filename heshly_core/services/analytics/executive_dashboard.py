from __future__ import annotations

from heshly_core.models.dashboard import (
    Dashboard,
    DashboardSection,
    DashboardType,
)

from heshly_core.services.analytics.dashboard_widgets import (
    DashboardWidgets,
)


class ExecutiveDashboard:
    """
    Executive Dashboard Builder.

    High-level business dashboard for owners and executives.

    Displays

        • Revenue
        • Profit
        • Customers
        • Appointments
        • Leads
        • Opportunities
        • Pipeline Value
        • Conversion Rate
        • Customer Retention
        • AI Accuracy
        • Monthly Revenue Trend
        • Sales by Month
        • Business Health
    """

    def __init__(self):

        self.widgets = DashboardWidgets()

    # =====================================================
    # Build Dashboard
    # =====================================================

    def build(
        self,
        data: dict | None = None,
    ) -> Dashboard:

        data = data or {}

        dashboard = Dashboard(

            dashboard_id="DASHBOARD-EXECUTIVE",

            name="Executive Dashboard",

            dashboard_type=DashboardType.EXECUTIVE,

            description="Executive business overview",

        )

        # =================================================
        # Executive KPIs
        # =================================================

        overview = DashboardSection(

            section_id="SECTION-OVERVIEW",

            title="Executive Overview",

        )

        overview.add_widget(
            self.widgets.kpi(
                "Revenue",
                data.get("revenue", 0),
                "KES",
            )
        )

        overview.add_widget(
            self.widgets.kpi(
                "Profit",
                data.get("profit", 0),
                "KES",
            )
        )

        overview.add_widget(
            self.widgets.kpi(
                "Customers",
                data.get("customers", 0),
            )
        )

        overview.add_widget(
            self.widgets.kpi(
                "Appointments",
                data.get("appointments", 0),
            )
        )

        dashboard.add_section(overview)

        # =================================================
        # Sales Performance
        # =================================================

        sales = DashboardSection(

            section_id="SECTION-SALES",

            title="Sales Performance",

        )

        sales.add_widget(
            self.widgets.number(
                "Leads",
                data.get("leads", 0),
            )
        )

        sales.add_widget(
            self.widgets.number(
                "Open Opportunities",
                data.get("opportunities", 0),
            )
        )

        sales.add_widget(
            self.widgets.metric(
                "Pipeline Value",
                data.get("pipeline_value", 0),
                "KES",
            )
        )

        sales.add_widget(
            self.widgets.progress(
                "Conversion Rate",
                data.get("conversion_rate", 0),
            )
        )

        dashboard.add_section(sales)

        # =================================================
        # Business Health
        # =================================================

        health = DashboardSection(

            section_id="SECTION-HEALTH",

            title="Business Health",

        )

        health.add_widget(
            self.widgets.gauge(
                "Customer Retention",
                data.get("customer_retention", 0),
            )
        )

        health.add_widget(
            self.widgets.gauge(
                "AI Accuracy",
                data.get("ai_accuracy", 0),
            )
        )

        health.add_widget(
            self.widgets.gauge(
                "Business Health",
                data.get("business_health", 0),
            )
        )

        dashboard.add_section(health)

        # =================================================
        # Trends
        # =================================================

        trends = DashboardSection(

            section_id="SECTION-TRENDS",

            title="Business Trends",

        )

        trends.add_widget(
            self.widgets.line_chart(
                "Monthly Revenue",
                data.get("monthly_revenue", []),
            )
        )

        trends.add_widget(
            self.widgets.area_chart(
                "Sales Trend",
                data.get("sales_trend", []),
            )
        )

        dashboard.add_section(trends)

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

            "type": dashboard.dashboard_type.value,

            "sections": dashboard.section_count,

            "widgets": dashboard.widget_count,

        }