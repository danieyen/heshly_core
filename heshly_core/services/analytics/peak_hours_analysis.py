from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime


class PeakHoursAnalysis:
    """
    Peak Hours Analysis

    Identifies:

        • Busiest hours
        • Busiest weekdays
        • Monthly demand
        • Staff workload by hour
        • Service demand by hour

    Expected appointment format:

    {
        "appointment_date": datetime(...),
        "employee_name": "...",
        "service_name": "...",
        "status": "completed"
    }
    """

    def analyze(
        self,
        appointments: list[dict],
    ) -> dict:

        hour_counter = Counter()
        weekday_counter = Counter()
        monthly_counter = Counter()

        staff_hour_counter = {}
        service_hour_counter = {}

        processed = 0

        for appointment in appointments:

            appointment_date = appointment.get(
                "appointment_date"
            )

            if not isinstance(
                appointment_date,
                datetime,
            ):
                continue

            processed += 1

            hour = appointment_date.hour

            weekday = appointment_date.strftime(
                "%A"
            )

            month = appointment_date.strftime(
                "%Y-%m"
            )

            hour_counter[hour] += 1

            weekday_counter[weekday] += 1

            monthly_counter[month] += 1

            employee = appointment.get(
                "employee_name",
                "Unknown",
            )

            if employee not in staff_hour_counter:

                staff_hour_counter[
                    employee
                ] = Counter()

            staff_hour_counter[
                employee
            ][hour] += 1

            service = appointment.get(
                "service_name",
                "Unknown",
            )

            if service not in service_hour_counter:

                service_hour_counter[
                    service
                ] = Counter()

            service_hour_counter[
                service
            ][hour] += 1

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "appointments": processed,

            "hourly_distribution": dict(
                sorted(hour_counter.items())
            ),

            "weekday_distribution": dict(
                weekday_counter
            ),

            "monthly_distribution": dict(
                monthly_counter
            ),

            "staff_hour_distribution": {

                employee: dict(counter)

                for employee, counter

                in staff_hour_counter.items()

            },

            "service_hour_distribution": {

                service: dict(counter)

                for service, counter

                in service_hour_counter.items()

            },

        }

    # =====================================================
    # Rankings
    # =====================================================

    def busiest_hours(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report["hourly_distribution"].items(),

            key=lambda x: x[1],

            reverse=True,

        )[:limit]

    def busiest_weekdays(
        self,
        report: dict,
        limit: int = 7,
    ):

        return sorted(

            report["weekday_distribution"].items(),

            key=lambda x: x[1],

            reverse=True,

        )[:limit]

    def busiest_months(
        self,
        report: dict,
        limit: int = 12,
    ):

        return sorted(

            report["monthly_distribution"].items(),

            key=lambda x: x[1],

            reverse=True,

        )[:limit]

    def busiest_staff(
        self,
        report: dict,
    ):

        ranking = []

        for employee, hours in report[
            "staff_hour_distribution"
        ].items():

            ranking.append(

                (
                    employee,

                    sum(hours.values()),
                )

            )

        ranking.sort(

            key=lambda x: x[1],

            reverse=True,

        )

        return ranking

    def busiest_services(
        self,
        report: dict,
    ):

        ranking = []

        for service, hours in report[
            "service_hour_distribution"
        ].items():

            ranking.append(

                (
                    service,

                    sum(hours.values()),
                )

            )

        ranking.sort(

            key=lambda x: x[1],

            reverse=True,

        )

        return ranking

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ) -> dict:

        return {

            "appointments": report[
                "appointments"
            ],

            "peak_hour": self.busiest_hours(
                report,
                1,
            ),

            "peak_day": self.busiest_weekdays(
                report,
                1,
            ),

            "peak_month": self.busiest_months(
                report,
                1,
            ),

            "top_staff": self.busiest_staff(
                report
            )[:3],

            "top_services": self.busiest_services(
                report
            )[:3],

        }