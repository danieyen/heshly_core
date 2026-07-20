from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from heshly_core.models.appointment_analytics import (
    AppointmentAnalyticsReport,
    AnalyticsPeriod,
    AppointmentStatusMetrics,
    DailyAppointmentAnalytics,
    ServiceAnalytics,
    StaffAnalytics,
)


class BookingAnalytics:
    """
    Booking Analytics Engine

    Calculates booking statistics from appointment records.

    Expected appointment dictionary:

    {
        "appointment_id": "...",
        "business_id": "...",
        "service_id": "...",
        "service_name": "...",
        "employee_id": "...",
        "employee_name": "...",
        "status": "completed",
        "amount": 5000,
        "duration": 60,
        "appointment_date": datetime(...)
    }
    """

    def generate(
        self,
        business_id: str,
        appointments: list[dict],
        period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY,
    ) -> AppointmentAnalyticsReport:

        report = AppointmentAnalyticsReport(

            report_id=f"BOOKING-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",

            business_id=business_id,

            period=period,

        )

        status = AppointmentStatusMetrics()

        service_stats = {}

        staff_stats = {}

        daily_stats = defaultdict(
            lambda: {
                "appointments": 0,
                "completed": 0,
                "cancelled": 0,
                "no_show": 0,
                "revenue": 0.0,
            }
        )

        revenue = 0.0

        # ==================================================
        # Aggregate
        # ==================================================

        for appt in appointments:

            appointment_status = (
                appt.get(
                    "status",
                    "scheduled",
                )
                .lower()
                .replace("-", "_")
            )

            if hasattr(status, appointment_status):

                setattr(

                    status,

                    appointment_status,

                    getattr(
                        status,
                        appointment_status,
                    )
                    + 1,

                )

            amount = float(
                appt.get(
                    "amount",
                    0,
                )
            )

            duration = float(
                appt.get(
                    "duration",
                    0,
                )
            )

            revenue += amount

            # ----------------------------------------------
            # Service
            # ----------------------------------------------

            sid = appt.get(
                "service_id",
                "UNKNOWN",
            )

            if sid not in service_stats:

                service_stats[sid] = ServiceAnalytics(

                    service_id=sid,

                    service_name=appt.get(
                        "service_name",
                        sid,
                    ),

                )

            service = service_stats[sid]

            service.appointments += 1

            service.revenue += amount

            service.average_duration += duration

            if appointment_status == "completed":

                service.completed += 1

            elif appointment_status == "cancelled":

                service.cancelled += 1

            # ----------------------------------------------
            # Staff
            # ----------------------------------------------

            eid = appt.get(
                "employee_id",
                "UNKNOWN",
            )

            if eid not in staff_stats:

                staff_stats[eid] = StaffAnalytics(

                    employee_id=eid,

                    employee_name=appt.get(
                        "employee_name",
                        eid,
                    ),

                )

            employee = staff_stats[eid]

            employee.appointments += 1

            if appointment_status == "completed":

                employee.completed += 1

            elif appointment_status == "cancelled":

                employee.cancelled += 1

            elif appointment_status == "no_show":

                employee.no_show += 1

            # ----------------------------------------------
            # Daily
            # ----------------------------------------------

            appointment_date = appt.get(
                "appointment_date",
                datetime.now(UTC),
            )

            day_key = appointment_date.date()

            daily = daily_stats[day_key]

            daily["appointments"] += 1

            daily["revenue"] += amount

            if appointment_status == "completed":

                daily["completed"] += 1

            elif appointment_status == "cancelled":

                daily["cancelled"] += 1

            elif appointment_status == "no_show":

                daily["no_show"] += 1

        # ==================================================
        # Finalize Services
        # ==================================================

        for service in service_stats.values():

            if service.appointments:

                service.average_duration /= (
                    service.appointments
                )

            report.add_service(service)

        # ==================================================
        # Finalize Staff
        # ==================================================

        for employee in staff_stats.values():

            if employee.appointments:

                employee.utilization = round(

                    (
                        employee.completed
                        / employee.appointments
                    )
                    * 100,

                    2,

                )

            report.add_staff(employee)

        # ==================================================
        # Finalize Daily
        # ==================================================

        for day, values in sorted(
            daily_stats.items()
        ):

            report.add_daily_record(

                DailyAppointmentAnalytics(

                    date=datetime.combine(
                        day,
                        datetime.min.time(),
                        tzinfo=UTC,
                    ),

                    appointments=values[
                        "appointments"
                    ],

                    completed=values[
                        "completed"
                    ],

                    cancelled=values[
                        "cancelled"
                    ],

                    no_show=values[
                        "no_show"
                    ],

                    revenue=values[
                        "revenue"
                    ],

                )

            )

        # ==================================================
        # Report Metrics
        # ==================================================

        total = status.total or 1

        report.status_metrics = status

        report.total_revenue = revenue

        report.average_booking_rate = 100.0

        report.completion_rate = round(
            status.completed / total * 100,
            2,
        )

        report.cancellation_rate = round(
            status.cancelled / total * 100,
            2,
        )

        report.no_show_rate = round(
            status.no_show / total * 100,
            2,
        )

        return report

    # ======================================================
    # Summary
    # ======================================================

    def summary(
        self,
        report: AppointmentAnalyticsReport,
    ) -> dict:

        return {

            "business": report.business_id,

            "period": report.period.value,

            "appointments": report.status_metrics.total,

            "revenue": report.total_revenue,

            "completion_rate": report.completion_rate,

            "cancellation_rate": report.cancellation_rate,

            "no_show_rate": report.no_show_rate,

            "services": report.total_services,

            "staff": report.total_staff,

            "days": report.total_days,

        }