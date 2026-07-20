from heshly_core.models.booking import (
    BookingOption,
)


class BookingConflictResolver:
    """
    Resolves booking conflicts by selecting
    an alternative booking option.
    """

    def resolve(
        self,
        options: list[BookingOption],
    ) -> BookingOption | None:

        if not options:
            return None

        return options[0]