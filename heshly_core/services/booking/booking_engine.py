from heshly_core.models.booking import (
    BookingRequest,
    BookingResult,
    BookingAction,
)

from heshly_core.services.booking.service_selector import (
    ServiceSelector,
)

from heshly_core.services.booking.staff_assignment import (
    StaffAssignment,
    StaffMember,
)

from heshly_core.services.booking.availability_checker import (
    AvailabilityChecker,
    BookedSlot,
)

from heshly_core.services.booking.time_slot_generator import (
    TimeSlotGenerator,
    AvailableSlot,
)

from heshly_core.services.booking.recommendation_engine import (
    BookingRecommendationEngine,
)

from heshly_core.services.booking.conflict_resolver import (
    BookingConflictResolver,
)

from heshly_core.services.booking.booking_confirmation_manager import (
    BookingConfirmationManager,
)

from heshly_core.services.booking.booking_conversation_flow import (
    BookingConversationFlow,
)


class BookingEngine:
    """
    Coordinates the complete booking process.
    """

    def __init__(
        self,
        selector: ServiceSelector | None = None,
        assignment: StaffAssignment | None = None,
        availability: AvailabilityChecker | None = None,
        generator: TimeSlotGenerator | None = None,
        recommender: BookingRecommendationEngine | None = None,
        resolver: BookingConflictResolver | None = None,
        confirmation: BookingConfirmationManager | None = None,
        flow: BookingConversationFlow | None = None,
    ):
        self.selector = selector or ServiceSelector()
        self.assignment = assignment or StaffAssignment()
        self.availability = (
            availability or AvailabilityChecker()
        )
        self.generator = (
            generator or TimeSlotGenerator()
        )
        self.recommender = (
            recommender
            or BookingRecommendationEngine()
        )
        self.resolver = (
            resolver
            or BookingConflictResolver()
        )
        self.confirmation = (
            confirmation
            or BookingConfirmationManager()
        )
        self.flow = (
            flow
            or BookingConversationFlow()
        )

    def book(
        self,
        request: BookingRequest,
        available_services: list[str],
        staff_members: list[StaffMember],
        booked_slots: list[BookedSlot],
        available_slots: list[AvailableSlot],
    ) -> tuple[
        BookingResult,
        BookingAction,
        str | None,
    ]:

        result = BookingResult(
            request=request
        )

        # -----------------------------
        # Resolve service
        # -----------------------------

        service = self.selector.select(
            request,
            available_services,
        )

        if service is None:
            result.reason = (
                "Requested service is unavailable."
            )

            action, message = self.flow.next_step(
                result
            )

            return (
                result,
                action,
                message,
            )

        request.service = service

        # -----------------------------
        # Assign staff
        # -----------------------------

        staff = self.assignment.assign(
            request,
            staff_members,
        )

        # -----------------------------
        # Requested slot available?
        # -----------------------------

        available = self.availability.is_available(
            request,
            staff,
            booked_slots,
        )

        if available:

            option = self.resolver.resolve(
                self.generator.generate(
                    request,
                    staff,
                    [
                        AvailableSlot(
                            date=request.preferred_date,
                            time=request.preferred_time,
                        )
                    ],
                )
            )

            result = self.confirmation.confirm(
                result,
                option,
            )

        else:

            result.options = self.recommender.recommend(
                request,
                self.generator.generate(
                    request,
                    staff,
                    available_slots,
                ),
            )

        action, message = self.flow.next_step(
            result
        )

        return (
            result,
            action,
            message,
        )