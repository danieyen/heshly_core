from heshly_core.models.learning import (
    CustomerFeedback,
    FeedbackRating,
)


class CustomerFeedbackCollector:
    """
    Collects customer feedback after a conversation.
    """

    def collect(
        self,
        *,
        conversation_id: str,
        customer_id: str,
        rating: FeedbackRating,
        comment: str | None = None,
        would_recommend: bool | None = None,
    ) -> CustomerFeedback:

        return CustomerFeedback(
            conversation_id=conversation_id,
            customer_id=customer_id,
            rating=rating,
            comment=comment,
            would_recommend=would_recommend,
        )

    def is_positive(
        self,
        feedback: CustomerFeedback,
    ) -> bool:

        return feedback.rating.value >= FeedbackRating.GOOD.value