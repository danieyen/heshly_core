from dataclasses import dataclass

from heshly_core.models.booking import (
    BookingRequest,
)

from heshly_core.services.booking.staff_assignment import (
    StaffMember,
)


@dataclass(slots=True)
class BookedSlot:
    """
    Represents an existing appointment.
    """

    staff: str

    date: str

    time: str


class AvailabilityChecker:
    """
    Checks whether a requested booking slot
    is available.
    """

    def is_available(
        self,
        request: BookingRequest,
        staff: StaffMember | None,
        booked_slots: list[BookedSlot],
    ) -> bool:

        if staff is None:
            return False

        if not request.preferred_date:
            return False

        if not request.preferred_time:
            return False

        for slot in booked_slots:

            if (
                slot.staff == staff.name
                and slot.date == request.preferred_date
                and slot.time == request.preferred_time
            ):
                return False

        return True