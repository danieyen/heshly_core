from heshly_core.models.handover import (
    ConversationSummary,
)


class ConversationSummaryBuilder:
    """
    Builds a structured summary for the receiving human agent.
    """

    def build(
        self,
        *,
        customer_name: str | None,
        customer_phone: str | None,
        requested_service: str | None,
        qualification_status: str | None,
        urgency: str | None,
        booking_recommendation: str | None,
        escalation_reason: str | None,
    ) -> ConversationSummary:

        lines = []

        if requested_service:
            lines.append(
                f"Requested service: {requested_service}."
            )

        if qualification_status:
            lines.append(
                f"Qualification: {qualification_status}."
            )

        if urgency:
            lines.append(
                f"Urgency: {urgency}."
            )

        if booking_recommendation:
            lines.append(
                f"Recommendation: {booking_recommendation}."
            )

        if escalation_reason:
            lines.append(
                f"Escalated because: {escalation_reason}."
            )

        return ConversationSummary(
            customer_name=customer_name,
            customer_phone=customer_phone,
            requested_service=requested_service,
            qualification_status=qualification_status,
            urgency=urgency,
            booking_recommendation=booking_recommendation,
            escalation_reason=escalation_reason,
            summary=" ".join(lines),
        )