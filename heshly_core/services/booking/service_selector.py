from heshly_core.models.booking import (
    BookingRequest,
)


class ServiceSelector:
    """
    Selects the best matching business service
    for a booking request.
    """

    def select(
        self,
        request: BookingRequest,
        available_services: list[str],
    ) -> str | None:

        if request.service is None:
            return None

        requested = request.service.strip().lower()

        # Exact match
        for service in available_services:

            if service.lower() == requested:
                return service

        # Partial match
        for service in available_services:

            if (
                requested in service.lower()
                or service.lower() in requested
            ):
                return service

        return None