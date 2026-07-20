from dataclasses import dataclass, field


@dataclass(slots=True)
class CustomerProfile:
    """
    Structured customer profile for AI context.
    """

    customer_id: str

    identity: dict[str, str] = field(
        default_factory=dict
    )

    preferences: list[str] = field(
        default_factory=list
    )

    behavior: list[str] = field(
        default_factory=list
    )

    history: list[str] = field(
        default_factory=list
    )

    temporary: list[str] = field(
        default_factory=list
    )