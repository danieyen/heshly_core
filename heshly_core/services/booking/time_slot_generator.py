from dataclasses import dataclass

from heshly_core.models.booking import (
    BookingOption,
    BookingRequest,
)

from heshly_core.services.booking.staff_assignment import (
    StaffMember,
)


@dataclass(slots=True)
class AvailableSlot:
    """
    Represents one available appointment slot.
    """

    date: str

    time: str


class TimeSlotGenerator:
    """
    Generates booking options from available slots.
    """

    def generate(
        self,
        request: BookingRequest,
        staff: StaffMember | None,
        available_slots: list[AvailableSlot],
    ) -> list[BookingOption]:

        if staff is None:
            return []

        if request.service is None:
            return []

        options: list[BookingOption] = []

        for slot in available_slots:

            option = BookingOption(
                service=request.service,
                staff=staff.name,
                date=slot.date,
                time=slot.time,
            )

            options.append(option)

        return options