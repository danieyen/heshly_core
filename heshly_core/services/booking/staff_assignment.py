from dataclasses import dataclass

from heshly_core.models.booking import (
    BookingRequest,
)


@dataclass(slots=True)
class StaffMember:
    """
    Staff member available for booking.
    """

    name: str

    services: list[str]


class StaffAssignment:
    """
    Selects the best staff member for a booking.
    """

    def assign(
        self,
        request: BookingRequest,
        staff_members: list[StaffMember],
    ) -> StaffMember | None:

        if not staff_members:
            return None

        # ----------------------------------
        # Customer requested a staff member
        # ----------------------------------

        if request.preferred_staff:

            preferred = (
                request.preferred_staff
                .strip()
                .lower()
            )

            for staff in staff_members:

                if (
                    staff.name.lower()
                    == preferred
                ):

                    if (
                        request.service is None
                        or request.service in staff.services
                    ):
                        return staff

        # ----------------------------------
        # Find first qualified staff member
        # ----------------------------------

        for staff in staff_members:

            if (
                request.service is None
                or request.service in staff.services
            ):
                return staff

        return None