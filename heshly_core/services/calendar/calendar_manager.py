from __future__ import annotations

from heshly_core.models.calendar import (
    AppointmentRequest,
    AvailabilityRequest,
)

from heshly_core.services.calendar.appointment_manager import (
    AppointmentManager,
)

from heshly_core.services.calendar.availability_engine import (
    AvailabilityEngine,
)

from heshly_core.services.calendar.business_hours_manager import (
    BusinessHours,
    BusinessHoursManager,
)

from heshly_core.services.calendar.calendar_conversation_flow import (
    CalendarConversationFlow,
)

from heshly_core.services.calendar.conflict_detector import (
    ConflictDetector,
)

from heshly_core.services.calendar.scheduling_engine import (
    SchedulingEngine,
)


class CalendarManager:
    """
    High-level façade for the calendar
    and scheduling subsystem.
    """

    def __init__(
        self,
    ) -> None:

        self.availability = AvailabilityEngine()

        self.conflicts = ConflictDetector()

        self.business_hours = (
            BusinessHoursManager()
        )

        self.appointments = (
            AppointmentManager()
        )

        self.scheduler = (
            SchedulingEngine(
                availability_engine=self.availability,
                appointment_manager=self.appointments,
            )
        )

        self.conversation = (
            CalendarConversationFlow(
                scheduling_engine=self.scheduler,
            )
        )

    def check_availability(
        self,
        request: AvailabilityRequest,
        events,
        working_start,
        working_end,
    ):

        return self.scheduler.check_availability(

            request=request,

            events=events,

            working_start=working_start,

            working_end=working_end,
        )

    def book(
        self,
        request: AppointmentRequest,
        events,
    ):

        return self.conversation.book_appointment(

            request,

            events,
        )

    def cancel(
        self,
        appointment_id: str,
    ):

        return self.conversation.cancel_appointment(

            appointment_id,
        )

    def reschedule(
        self,
        request: AppointmentRequest,
        events,
    ):

        return self.conversation.reschedule_appointment(

            request,

            events,
        )

    def validate_business_hours(
        self,
        request: AppointmentRequest,
        hours: BusinessHours,
    ):

        return self.business_hours.is_within_hours(

            request,

            hours,
        )

    def detect_conflicts(
        self,
        request: AppointmentRequest,
        events,
    ):

        return self.conflicts.detect(

            request,

            events,
        )