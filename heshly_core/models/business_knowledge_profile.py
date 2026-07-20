from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class BusinessKnowledgeProfile:
    """
    Business Knowledge Profile.

    Represents the business knowledge
    available to the AI for one tenant.
    """

    profile_id: str

    tenant_id: str

    business_name: str

    industry: str

    description: str = ""

    services: list[str] = field(
        default_factory=list
    )

    products: list[str] = field(
        default_factory=list
    )

    faqs: list[str] = field(
        default_factory=list
    )

    policies: list[str] = field(
        default_factory=list
    )

    business_hours: dict[str, str] = field(
        default_factory=dict
    )

    contact_information: dict[str, str] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def add_service(
        self,
        service: str,
    ):

        if service not in self.services:

            self.services.append(service)

            self.updated_at = datetime.now(UTC)

    def add_product(
        self,
        product: str,
    ):

        if product not in self.products:

            self.products.append(product)

            self.updated_at = datetime.now(UTC)

    def add_faq(
        self,
        faq: str,
    ):

        self.faqs.append(faq)

        self.updated_at = datetime.now(UTC)

    def add_policy(
        self,
        policy: str,
    ):

        self.policies.append(policy)

        self.updated_at = datetime.now(UTC)