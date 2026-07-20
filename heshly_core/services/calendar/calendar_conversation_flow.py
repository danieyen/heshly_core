from __future__ import annotations

from dataclasses import dataclass

from heshly_core.models.calendar import (
    AppointmentRequest,
    AppointmentResult,
)

from heshly_core.services.calendar.scheduling_engine import (
    SchedulingEngine,
)


@dataclass(slots=True)
class CalendarConversationResult:
    """
    Result returned to the AI Receptionist.
    """

    success: bool

    response: str

    appointment: AppointmentResult | None = None


class CalendarConversationFlow:
    """
    Orchestrates calendar conversations.

    Responsible for turning booking
    requests into scheduling operations.
    """

    def __init__(
        self,
        scheduling_engine: SchedulingEngine | None = None,
    ) -> None:

        self._scheduler = (
            scheduling_engine
            or SchedulingEngine()
        )

    def book_appointment(
        self,
        request: AppointmentRequest,
        events,
    ) -> CalendarConversationResult:

        result = self._scheduler.schedule(

            request=request,

            events=events,
        )

        if result.success:

            return CalendarConversationResult(

                success=True,

                response=(
                    "Your appointment has been booked successfully."
                ),

                appointment=result,
            )

        return CalendarConversationResult(

            success=False,

            response=result.message,

            appointment=result,
        )

    def cancel_appointment(
        self,
        appointment_id: str,
    ) -> CalendarConversationResult:

        #
        # Future:
        # Delegate to AppointmentManager.
        #

        return CalendarConversationResult(

            success=True,

            response="Appointment cancelled.",
        )

    def reschedule_appointment(
        self,
        request: AppointmentRequest,
        events,
    ) -> CalendarConversationResult:

        #
        # Future:
        # Cancel existing appointment
        # then create a new one.
        #

        return self.book_appointment(

            request,

            events,
        )