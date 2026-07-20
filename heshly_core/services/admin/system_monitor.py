from __future__ import annotations

from datetime import UTC, datetime


class SystemMonitor:
    """
    Heshly Platform System Monitor.

    Collects health information from
    platform services.
    """

    def __init__(self):

        self.services = {}


    # =====================================================
    # Register Service
    # =====================================================

    def register_service(
        self,
        name: str,
        service,
    ):

        self.services[name] = service


    # =====================================================
    # Check Service
    # =====================================================

    def check_service(
        self,
        name: str,
    ) -> dict:

        service = self.services.get(
            name
        )

        if service is None:

            return {

                "service": name,

                "status": "unknown",

            }


        if hasattr(service, "health"):

            return service.health()


        return {

            "service": name,

            "status": "unavailable",

        }


    # =====================================================
    # Full System Check
    # =====================================================

    def health_report(self):

        results = {}

        for name in self.services:

            results[name] = (
                self.check_service(name)
            )


        return {

            "timestamp":
                datetime.now(UTC),

            "services":
                results,

        }


    # =====================================================
    # System Status
    # =====================================================

    def system_status(self):

        report = self.health_report()

        failed = []

        for name, service in (
            report["services"].items()
        ):

            if service.get("status") != "healthy":

                failed.append(
                    name
                )


        return {

            "status":
                "healthy"
                if not failed
                else "degraded",

            "failed_services":
                failed,

        }


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "system_monitor",

            "status":
                "healthy",

        }