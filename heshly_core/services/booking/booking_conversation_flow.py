from heshly_core.models.booking import (
    BookingAction,
    BookingResult,
    BookingStatus,
)


class BookingConversationFlow:
    """
    Determines the next booking conversation step.
    """

    def next_step(
        self,
        result: BookingResult,
    ) -> tuple[
        BookingAction,
        str | None,
    ]:

        if result.status == BookingStatus.CONFIRMED:

            return (
                BookingAction.CONFIRM_BOOKING,
                "Your appointment has been confirmed.",
            )

        if result.status == BookingStatus.FAILED:

            return (
                BookingAction.END_CONVERSATION,
                result.reason,
            )

        if result.options:

            return (
                BookingAction.PRESENT_OPTIONS,
                "Here are the available appointment options.",
            )

        return (
            BookingAction.ASK_INFORMATION,
            "Could you provide your preferred date and time?",
        )