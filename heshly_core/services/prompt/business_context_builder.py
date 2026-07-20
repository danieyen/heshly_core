from heshly_core.models.knowledge import (
    ServiceInfo,
)


class BusinessContextBuilder:
    """
    Builds the business context portion of the AI prompt.
    """

    def build(
        self,
        business_name: str,
        business_type: str,
        services: list[ServiceInfo],
        description: str | None = None,
        business_hours: str | None = None,
        booking_policy: str | None = None,
    ) -> str:

        lines = [
            "Business Context:",
            "",
            f"Business: {business_name}",
            f"Industry: {business_type}",
        ]

        if description:
            lines.append(
                f"Description: {description}"
            )

        lines.append("")
        lines.append("Services:")

        if services:

            for service in services:

                text = f"- {service.name}"

                if service.duration_minutes is not None:
                    text += (
                        f" ({service.duration_minutes} min)"
                    )

                if service.price is not None:
                    text += (
                        f" - {service.price}"
                    )

                lines.append(text)

        else:

            lines.append(
                "- No services configured."
            )

        if business_hours:

            lines.extend(
                [
                    "",
                    "Business Hours:",
                    business_hours,
                ]
            )

        if booking_policy:

            lines.extend(
                [
                    "",
                    "Booking Policy:",
                    booking_policy,
                ]
            )

        return "\n".join(lines)