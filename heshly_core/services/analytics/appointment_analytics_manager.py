from __future__ import annotations

from heshly_core.models.appointment_analytics import (
    AnalyticsPeriod,
)

from heshly_core.services.analytics.booking_analytics import (
    BookingAnalytics,
)

from heshly_core.services.analytics.cancellation_analytics import (
    CancellationAnalytics,
)

from heshly_core.services.analytics.no_show_analytics import (
    NoShowAnalytics,
)

from heshly_core.services.analytics.utilization_analytics import (
    UtilizationAnalytics,
)

from heshly_core.services.analytics.peak_hours_analysis import (
    PeakHoursAnalysis,
)

from heshly_core.services.analytics.appointment_forecasting import (
    AppointmentForecasting,
)


class AppointmentAnalyticsManager:
    """
    Central Appointment Analytics Manager.

    Coordinates every appointment analytics component.

    Modules

        • Booking Analytics
        • Cancellation Analytics
        • No-show Analytics
        • Utilization Analytics
        • Peak Hours Analysis
        • Appointment Forecasting
    """

    def __init__(self):

        self.booking = BookingAnalytics()

        self.cancellations = CancellationAnalytics()

        self.no_shows = NoShowAnalytics()

        self.utilization = UtilizationAnalytics()

        self.peak_hours = PeakHoursAnalysis()

        self.forecasting = AppointmentForecasting()

    # =====================================================
    # Booking
    # =====================================================

    def booking_report(
        self,
        business_id: str,
        appointments: list[dict],
        period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY,
    ):

        return self.booking.generate(
            business_id,
            appointments,
            period,
        )

    # =====================================================
    # Cancellation
    # =====================================================

    def cancellation_report(
        self,
        appointments: list[dict],
    ):

        return self.cancellations.analyze(
            appointments
        )

    # =====================================================
    # No Show
    # =====================================================

    def no_show_report(
        self,
        appointments: list[dict],
    ):

        return self.no_shows.analyze(
            appointments
        )

    # =====================================================
    # Utilization
    # =====================================================

    def utilization_report(
        self,
        appointments: list[dict],
        employee_capacity: int = 480,
        room_capacity: int = 480,
        service_capacity: int = 480,
    ):

        return self.utilization.analyze(

            appointments,

            available_minutes_per_employee=employee_capacity,

            available_minutes_per_room=room_capacity,

            available_minutes_per_service=service_capacity,

        )

    # =====================================================
    # Peak Hours
    # =====================================================

    def peak_hours_report(
        self,
        appointments: list[dict],
    ):

        return self.peak_hours.analyze(
            appointments
        )

    # =====================================================
    # Forecast
    # =====================================================

    def forecast(
        self,
        history: list[dict],
        periods: int = 7,
    ):

        return self.forecasting.forecast(
            history,
            periods,
        )

    # =====================================================
    # Complete Analytics
    # =====================================================

    def complete_report(
        self,
        business_id: str,
        appointments: list[dict],
        history: list[dict],
        period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY,
    ) -> dict:

        booking = self.booking_report(
            business_id,
            appointments,
            period,
        )

        cancellations = self.cancellation_report(
            appointments
        )

        no_shows = self.no_show_report(
            appointments
        )

        utilization = self.utilization_report(
            appointments
        )

        peak = self.peak_hours_report(
            appointments
        )

        forecast = self.forecast(
            history
        )

        return {

            "booking": booking,

            "cancellations": cancellations,

            "no_shows": no_shows,

            "utilization": utilization,

            "peak_hours": peak,

            "forecast": forecast,

        }

    # =====================================================
    # Health Check
    # =====================================================

    def health(self):

        return {

            "status": "healthy",

            "modules": {

                "booking": True,

                "cancellation": True,

                "no_show": True,

                "utilization": True,

                "peak_hours": True,

                "forecasting": True,

            },

        }

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ):

        booking = report["booking"]

        return {

            "appointments": booking.status_metrics.total,

            "revenue": booking.total_revenue,

            "completion_rate": booking.completion_rate,

            "cancellation_rate": booking.cancellation_rate,

            "no_show_rate": booking.no_show_rate,

            "overall_utilization": report[
                "utilization"
            ][
                "overall_utilization"
            ],

            "forecast_trend": report[
                "forecast"
            ][
                "trend"
            ],

            "health": self.health(),

        }