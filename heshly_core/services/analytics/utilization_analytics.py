from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime


class UtilizationAnalytics:
    """
    Utilization Analytics

    Calculates staff, room and service utilization.

    Expected appointment structure:

    {
        "appointment_id": "...",
        "employee_id": "...",
        "employee_name": "...",
        "room": "...",
        "service_name": "...",
        "duration": 60,              # minutes
        "status": "completed"
    }
    """

    def analyze(
        self,
        appointments: list[dict],
        available_minutes_per_employee: int = 480,
        available_minutes_per_room: int = 480,
        available_minutes_per_service: int = 480,
    ) -> dict:

        employee_usage = defaultdict(
            lambda: {
                "appointments": 0,
                "minutes": 0,
            }
        )

        room_usage = defaultdict(
            lambda: {
                "appointments": 0,
                "minutes": 0,
            }
        )

        service_usage = defaultdict(
            lambda: {
                "appointments": 0,
                "minutes": 0,
            }
        )

        total_minutes = 0

        completed = 0

        for appointment in appointments:

            if (
                appointment.get(
                    "status",
                    "",
                ).lower()
                != "completed"
            ):
                continue

            completed += 1

            duration = float(
                appointment.get(
                    "duration",
                    0,
                )
            )

            total_minutes += duration

            # =============================================
            # Employee
            # =============================================

            employee = appointment.get(
                "employee_name",
                "Unknown",
            )

            employee_usage[employee][
                "appointments"
            ] += 1

            employee_usage[employee][
                "minutes"
            ] += duration

            # =============================================
            # Room
            # =============================================

            room = appointment.get(
                "room",
                "Default",
            )

            room_usage[room][
                "appointments"
            ] += 1

            room_usage[room][
                "minutes"
            ] += duration

            # =============================================
            # Service
            # =============================================

            service = appointment.get(
                "service_name",
                "Unknown",
            )

            service_usage[service][
                "appointments"
            ] += 1

            service_usage[service][
                "minutes"
            ] += duration

        # =============================================
        # Employee Utilization
        # =============================================

        employees = {}

        for name, values in employee_usage.items():

            utilization = round(

                values["minutes"]
                / available_minutes_per_employee
                * 100,

                2,

            )

            employees[name] = {

                **values,

                "utilization": utilization,

            }

        # =============================================
        # Room Utilization
        # =============================================

        rooms = {}

        for room, values in room_usage.items():

            utilization = round(

                values["minutes"]
                / available_minutes_per_room
                * 100,

                2,

            )

            rooms[room] = {

                **values,

                "utilization": utilization,

            }

        # =============================================
        # Service Utilization
        # =============================================

        services = {}

        for service, values in service_usage.items():

            utilization = round(

                values["minutes"]
                / available_minutes_per_service
                * 100,

                2,

            )

            services[service] = {

                **values,

                "utilization": utilization,

            }

        overall = round(

            total_minutes
            / (
                max(
                    len(employee_usage),
                    1,
                )
                * available_minutes_per_employee
            )
            * 100,

            2,

        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "completed_appointments": completed,

            "total_minutes": total_minutes,

            "overall_utilization": overall,

            "employees": employees,

            "rooms": rooms,

            "services": services,

        }

    # =====================================================
    # Rankings
    # =====================================================

    def top_employees(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report["employees"].items(),

            key=lambda x: x[1]["utilization"],

            reverse=True,

        )[:limit]

    def top_rooms(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report["rooms"].items(),

            key=lambda x: x[1]["utilization"],

            reverse=True,

        )[:limit]

    def top_services(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report["services"].items(),

            key=lambda x: x[1]["utilization"],

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

            "completed_appointments": report[
                "completed_appointments"
            ],

            "overall_utilization": report[
                "overall_utilization"
            ],

            "employees": len(
                report["employees"]
            ),

            "rooms": len(
                report["rooms"]
            ),

            "services": len(
                report["services"]
            ),

            "top_employee": self.top_employees(
                report,
                1,
            ),

            "top_room": self.top_rooms(
                report,
                1,
            ),

            "top_service": self.top_services(
                report,
                1,
            ),

        }