from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime


class CancellationAnalytics:
    """
    Cancellation Analytics

    Analyzes cancelled appointments to identify trends,
    cancellation rates, reasons, timing, and affected services.

    Expected appointment format:

    {
        "appointment_id": "...",
        "service_name": "...",
        "employee_name": "...",
        "customer_name": "...",
        "status": "cancelled",
        "reason": "Client Sick",
        "appointment_date": datetime(...),
        "cancelled_at": datetime(...)
    }
    """

    def analyze(
        self,
        appointments: list[dict],
    ) -> dict:

        total = len(appointments)

        cancelled = [
            a
            for a in appointments
            if a.get("status", "").lower() == "cancelled"
        ]

        cancellation_count = len(cancelled)

        cancellation_rate = round(
            (cancellation_count / total) * 100,
            2,
        ) if total else 0.0

        reasons = Counter()

        services = Counter()

        staff = Counter()

        weekday = Counter()

        monthly = Counter()

        notice_hours = []

        for appointment in cancelled:

            reasons[
                appointment.get(
                    "reason",
                    "Unknown",
                )
            ] += 1

            services[
                appointment.get(
                    "service_name",
                    "Unknown",
                )
            ] += 1

            staff[
                appointment.get(
                    "employee_name",
                    "Unknown",
                )
            ] += 1

            appointment_date = appointment.get(
                "appointment_date"
            )

            cancelled_at = appointment.get(
                "cancelled_at"
            )

            if isinstance(
                appointment_date,
                datetime,
            ):

                weekday[
                    appointment_date.strftime("%A")
                ] += 1

                monthly[
                    appointment_date.strftime("%Y-%m")
                ] += 1

            if (
                isinstance(
                    appointment_date,
                    datetime,
                )
                and isinstance(
                    cancelled_at,
                    datetime,
                )
            ):

                hours = (
                    appointment_date
                    - cancelled_at
                ).total_seconds() / 3600

                notice_hours.append(hours)

        average_notice = round(
            sum(notice_hours)
            / len(notice_hours),
            2,
        ) if notice_hours else 0.0

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "total_appointments": total,

            "cancelled": cancellation_count,

            "cancellation_rate": cancellation_rate,

            "average_notice_hours": average_notice,

            "reason_breakdown": dict(reasons),

            "service_breakdown": dict(services),

            "staff_breakdown": dict(staff),

            "weekday_breakdown": dict(weekday),

            "monthly_breakdown": dict(monthly),

        }

    # =====================================================
    # Top Lists
    # =====================================================

    def top_reasons(
        self,
        report: dict,
        limit: int = 5,
    ):

        items = sorted(

            report["reason_breakdown"].items(),

            key=lambda item: item[1],

            reverse=True,

        )

        return items[:limit]

    def top_services(
        self,
        report: dict,
        limit: int = 5,
    ):

        items = sorted(

            report["service_breakdown"].items(),

            key=lambda item: item[1],

            reverse=True,

        )

        return items[:limit]

    def top_staff(
        self,
        report: dict,
        limit: int = 5,
    ):

        items = sorted(

            report["staff_breakdown"].items(),

            key=lambda item: item[1],

            reverse=True,

        )

        return items[:limit]

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ) -> dict:

        return {

            "appointments": report[
                "total_appointments"
            ],

            "cancelled": report[
                "cancelled"
            ],

            "rate": report[
                "cancellation_rate"
            ],

            "average_notice_hours": report[
                "average_notice_hours"
            ],

            "top_reason": self.top_reasons(
                report,
                1,
            ),

            "top_service": self.top_services(
                report,
                1,
            ),

            "top_staff": self.top_staff(
                report,
                1,
            ),

        }