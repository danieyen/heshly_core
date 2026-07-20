from __future__ import annotations

from heshly_core.models.dashboard import (
    Dashboard,
    DashboardSection,
    DashboardType,
)

from heshly_core.services.analytics.dashboard_widgets import (
    DashboardWidgets,
)


class AppointmentDashboard:
    """
    Appointment Dashboard Builder.

    Displays

        • Total Appointments
        • Scheduled Today
        • Completed
        • Cancelled
        • No-shows
        • Booking Rate
        • Daily Appointment Trend
        • Weekly Appointment Trend
        • Appointments by Service
        • Appointments by Staff
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

            dashboard_id="DASHBOARD-APPOINTMENTS",

            name="Appointment Dashboard",

            dashboard_type=DashboardType.APPOINTMENTS,

            description="Appointment analytics dashboard",

        )

        # =================================================
        # Overview
        # =================================================

        overview = DashboardSection(

            section_id="SECTION-OVERVIEW",

            title="Appointment Overview",

        )

        overview.add_widget(

            self.widgets.kpi(

                "Total Appointments",

                data.get(

                    "total_appointments",

                    0,

                ),

            )

        )

        overview.add_widget(

            self.widgets.kpi(

                "Today's Appointments",

                data.get(

                    "today",

                    0,

                ),

            )

        )

        overview.add_widget(

            self.widgets.kpi(

                "Completed",

                data.get(

                    "completed",

                    0,

                ),

            )

        )

        overview.add_widget(

            self.widgets.kpi(

                "Cancelled",

                data.get(

                    "cancelled",

                    0,

                ),

            )

        )

        overview.add_widget(

            self.widgets.kpi(

                "No-shows",

                data.get(

                    "no_shows",

                    0,

                ),

            )

        )

        overview.add_widget(

            self.widgets.progress(

                "Booking Rate",

                data.get(

                    "booking_rate",

                    0,

                ),

            )

        )

        dashboard.add_section(

            overview

        )

        # =================================================
        # Trends
        # =================================================

        trends = DashboardSection(

            section_id="SECTION-TRENDS",

            title="Appointment Trends",

        )

        trends.add_widget(

            self.widgets.line_chart(

                "Daily Appointments",

                data.get(

                    "daily_trend",

                    [],

                ),

            )

        )

        trends.add_widget(

            self.widgets.area_chart(

                "Weekly Trend",

                data.get(

                    "weekly_trend",

                    [],

                ),

            )

        )

        dashboard.add_section(

            trends

        )

        # =================================================
        # Breakdown
        # =================================================

        breakdown = DashboardSection(

            section_id="SECTION-BREAKDOWN",

            title="Appointment Breakdown",

        )

        breakdown.add_widget(

            self.widgets.bar_chart(

                "Appointments by Service",

                data.get(

                    "service_breakdown",

                    [],

                ),

            )

        )

        breakdown.add_widget(

            self.widgets.pie_chart(

                "Appointments by Staff",

                data.get(

                    "staff_breakdown",

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