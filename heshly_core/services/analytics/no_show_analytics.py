from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime


class NoShowAnalytics:
    """
    No-show Analytics

    Analyzes appointment no-shows to identify patterns,
    customer behavior, affected services and staff.

    Expected appointment format:

    {
        "appointment_id": "...",
        "customer_id": "...",
        "customer_name": "...",
        "service_name": "...",
        "employee_name": "...",
        "status": "no_show",
        "appointment_date": datetime(...)
    }
    """

    def analyze(
        self,
        appointments: list[dict],
    ) -> dict:

        total = len(appointments)

        no_shows = [
            appointment
            for appointment in appointments
            if appointment.get("status", "").lower() == "no_show"
        ]

        no_show_count = len(no_shows)

        no_show_rate = (
            round((no_show_count / total) * 100, 2)
            if total
            else 0.0
        )

        customer_counter = Counter()
        service_counter = Counter()
        staff_counter = Counter()
        weekday_counter = Counter()
        monthly_counter = Counter()

        repeat_no_show_customers = {}

        for appointment in no_shows:

            customer = appointment.get(
                "customer_name",
                "Unknown",
            )

            service = appointment.get(
                "service_name",
                "Unknown",
            )

            employee = appointment.get(
                "employee_name",
                "Unknown",
            )

            customer_counter[customer] += 1
            service_counter[service] += 1
            staff_counter[employee] += 1

            appointment_date = appointment.get(
                "appointment_date"
            )

            if isinstance(appointment_date, datetime):

                weekday_counter[
                    appointment_date.strftime("%A")
                ] += 1

                monthly_counter[
                    appointment_date.strftime("%Y-%m")
                ] += 1

        for customer, count in customer_counter.items():

            if count > 1:

                repeat_no_show_customers[
                    customer
                ] = count

        return {

            "generated_at": datetime.now(UTC),

            "total_appointments": total,

            "no_shows": no_show_count,

            "no_show_rate": no_show_rate,

            "repeat_customers": repeat_no_show_customers,

            "customer_breakdown": dict(customer_counter),

            "service_breakdown": dict(service_counter),

            "staff_breakdown": dict(staff_counter),

            "weekday_breakdown": dict(weekday_counter),

            "monthly_breakdown": dict(monthly_counter),

        }

    # =====================================================
    # Rankings
    # =====================================================

    def top_repeat_customers(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report["repeat_customers"].items(),

            key=lambda item: item[1],

            reverse=True,

        )[:limit]

    def top_services(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report["service_breakdown"].items(),

            key=lambda item: item[1],

            reverse=True,

        )[:limit]

    def top_staff(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report["staff_breakdown"].items(),

            key=lambda item: item[1],

            reverse=True,

        )[:limit]

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

            "no_shows": report[
                "no_shows"
            ],

            "no_show_rate": report[
                "no_show_rate"
            ],

            "repeat_customers": len(
                report["repeat_customers"]
            ),

            "top_repeat_customer": self.top_repeat_customers(
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