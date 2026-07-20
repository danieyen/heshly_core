from __future__ import annotations

from datetime import timedelta

from heshly_core.models.calendar import (
    AppointmentRequest,
    AppointmentResult,
    AppointmentStatus,
    CalendarEvent,
)

from heshly_core.models.calendar_provider import (
    ProviderAppointmentResult,
)

from heshly_core.services.calendar.providers.provider_integration import (
    ProviderIntegration,
)


class AppointmentManager:
    """
    Manages appointments independently
    of the underlying calendar provider.
    """

    def __init__(
        self,
        provider: ProviderIntegration | None = None,
    ) -> None:

        self._provider = (
            provider
            or ProviderIntegration()
        )

    def create(
        self,
        request: AppointmentRequest,
    ) -> AppointmentResult:

        event = CalendarEvent(

            event_id="",

            title=request.service,

            start=request.start,

            end=(
                request.start
                + timedelta(
                    minutes=request.duration_minutes
                )
            ),

            customer_name=request.customer_name,

            customer_phone=request.customer_phone,

            notes=request.notes,

            status=AppointmentStatus.CONFIRMED,
        )

        result = self._provider.create_event(
            event
        )

        return self._build_result(
            result
        )

    def update(
        self,
        event: CalendarEvent,
    ) -> AppointmentResult:

        result = self._provider.update_event(
            event
        )

        return self._build_result(
            result
        )

    def cancel(
        self,
        appointment_id: str,
    ) -> AppointmentResult:

        result = self._provider.delete_event(
            appointment_id
        )

        return self._build_result(
            result
        )

    def _build_result(
        self,
        provider_result: ProviderAppointmentResult,
    ) -> AppointmentResult:

        return AppointmentResult(

            success=provider_result.success,

            appointment_id=(
                provider_result.event_id
            ),

            status=(
                AppointmentStatus.CONFIRMED
                if provider_result.success
                else None
            ),

            message=provider_result.message,
        )