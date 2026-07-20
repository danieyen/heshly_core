from heshly_core.models.booking import (
    BookingOption,
    BookingRequest,
)


class BookingRecommendationEngine:
    """
    Ranks booking options from best to worst.
    """

    def recommend(
        self,
        request: BookingRequest,
        options: list[BookingOption],
    ) -> list[BookingOption]:

        for option in options:

            score = option.score

            if (
                request.preferred_date
                and option.date == request.preferred_date
            ):
                score += 40

            if (
                request.preferred_time
                and option.time == request.preferred_time
            ):
                score += 40

            option.score = score

        return sorted(
            options,
            key=lambda option: option.score,
            reverse=True,
        )