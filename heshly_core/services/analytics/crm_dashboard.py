from __future__ import annotations

from heshly_core.models.dashboard import (
    Dashboard,
    DashboardSection,
    DashboardType,
)

from heshly_core.services.analytics.dashboard_widgets import (
    DashboardWidgets,
)


class CRMDashboard:
    """
    CRM Dashboard Builder.

    Displays

        • Total Leads
        • New Leads
        • Qualified Leads
        • Open Opportunities
        • Won Opportunities
        • Lost Opportunities
        • Pipeline Value
        • Lead Conversion Rate
        • Win Rate
        • Follow-ups Due
        • Recent Activities
        • Pipeline by Stage
        • Lead Sources
    """

    def __init__(self):

        self.widgets = DashboardWidgets()

    # =====================================================
    # Dashboard Builder
    # =====================================================

    def build(
        self,
        data: dict | None = None,
    ) -> Dashboard:

        data = data or {}

        dashboard = Dashboard(

            dashboard_id="DASHBOARD-CRM",

            name="CRM Dashboard",

            dashboard_type=DashboardType.CRM,

            description="CRM performance dashboard",

        )

        # =================================================
        # Lead Overview
        # =================================================

        overview = DashboardSection(

            section_id="SECTION-LEADS",

            title="Lead Overview",

        )

        overview.add_widget(

            self.widgets.kpi(

                "Total Leads",

                data.get(

                    "total_leads",

                    0,

                ),

            )

        )

        overview.add_widget(

            self.widgets.kpi(

                "New Leads",

                data.get(

                    "new_leads",

                    0,

                ),

            )

        )

        overview.add_widget(

            self.widgets.kpi(

                "Qualified Leads",

                data.get(

                    "qualified_leads",

                    0,

                ),

            )

        )

        overview.add_widget(

            self.widgets.progress(

                "Lead Conversion",

                data.get(

                    "lead_conversion_rate",

                    0,

                ),

            )

        )

        dashboard.add_section(

            overview

        )

        # =================================================
        # Opportunity Performance
        # =================================================

        opportunities = DashboardSection(

            section_id="SECTION-OPPORTUNITIES",

            title="Opportunity Performance",

        )

        opportunities.add_widget(

            self.widgets.number(

                "Open Opportunities",

                data.get(

                    "open_opportunities",

                    0,

                ),

            )

        )

        opportunities.add_widget(

            self.widgets.number(

                "Won Opportunities",

                data.get(

                    "won_opportunities",

                    0,

                ),

            )

        )

        opportunities.add_widget(

            self.widgets.number(

                "Lost Opportunities",

                data.get(

                    "lost_opportunities",

                    0,

                ),

            )

        )

        opportunities.add_widget(

            self.widgets.gauge(

                "Win Rate",

                data.get(

                    "win_rate",

                    0,

                ),

            )

        )

        dashboard.add_section(

            opportunities

        )

        # =================================================
        # Pipeline
        # =================================================

        pipeline = DashboardSection(

            section_id="SECTION-PIPELINE",

            title="Sales Pipeline",

        )

        pipeline.add_widget(

            self.widgets.metric(

                "Pipeline Value",

                data.get(

                    "pipeline_value",

                    0,

                ),

                "KES",

            )

        )

        pipeline.add_widget(

            self.widgets.bar_chart(

                "Pipeline by Stage",

                data.get(

                    "pipeline_stage_breakdown",

                    [],

                ),

            )

        )

        dashboard.add_section(

            pipeline

        )

        # =================================================
        # Activity
        # =================================================

        activity = DashboardSection(

            section_id="SECTION-ACTIVITY",

            title="Activities",

        )

        activity.add_widget(

            self.widgets.number(

                "Follow-ups Due",

                data.get(

                    "followups_due",

                    0,

                ),

            )

        )

        activity.add_widget(

            self.widgets.table(

                "Recent Activities",

                data.get(

                    "recent_activities",

                    [],

                ),

            )

        )

        dashboard.add_section(

            activity

        )

        # =================================================
        # Lead Sources
        # =================================================

        sources = DashboardSection(

            section_id="SECTION-SOURCES",

            title="Lead Sources",

        )

        sources.add_widget(

            self.widgets.pie_chart(

                "Lead Sources",

                data.get(

                    "lead_sources",

                    [],

                ),

            )

        )

        dashboard.add_section(

            sources

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