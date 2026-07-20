from __future__ import annotations


class ServiceContainer:
    """
    Base dependency injection container.

    Provides common functionality for
    subsystem service containers.
    """

    def __init__(self, **services):

        self._services = services

        for name, service in services.items():

            setattr(
                self,
                name,
                service,
            )

    # =====================================================
    # Access
    # =====================================================

    def get(
        self,
        name: str,
    ):

        return self._services.get(
            name
        )

    def has(
        self,
        name: str,
    ) -> bool:

        return name in self._services

    def names(
        self,
    ) -> list[str]:

        return sorted(
            self._services.keys()
        )

    def services(
        self,
    ) -> dict:

        return dict(
            self._services
        )

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        status = {}

        overall = "healthy"

        for name, service in self._services.items():

            if hasattr(
                service,
                "health",
            ):

                result = service.health()

                state = result.get(
                    "status",
                    "unknown",
                )

            else:

                state = "unknown"

            status[name] = state

            if state != "healthy":

                overall = "degraded"

        return {

            "service": self.__class__.__name__,

            "status": overall,

            "services": status,

        }