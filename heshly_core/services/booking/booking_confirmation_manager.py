from heshly_core.models.booking import (
    BookingOption,
    BookingResult,
    BookingStatus,
)


class BookingConfirmationManager:
    """
    Finalizes a booking.
    """

    def confirm(
        self,
        result: BookingResult,
        option: BookingOption | None,
    ) -> BookingResult:

        if option is None:

            result.status = BookingStatus.FAILED

            result.reason = (
                "No booking option available."
            )

            return result

        result.selected_option = option

        result.status = (
            BookingStatus.CONFIRMED
        )

        result.reason = None

        return result