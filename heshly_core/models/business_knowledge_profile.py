from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from heshly_core.models.knowledge import (
    KnowledgeContext,
    ServiceInfo,
)


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
        service = service.strip()

        if service and service not in self.services:
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

    def service_info(self) -> list[ServiceInfo]:
        """
        Convert configured service names into the richer
        ServiceInfo representation used by KnowledgeContext.

        BusinessKnowledgeProfile remains the source of configured
        service names. ServiceInfo provides the richer interface
        expected by knowledge consumers.
        """
        return [
            ServiceInfo(
                name=service,
                description=None,
                duration_minutes=None,
                price=None,
                active=True,
            )
            for service in self.services
        ]

    def knowledge_context(self) -> KnowledgeContext:
        """
        Build a KnowledgeContext from this business knowledge profile.
        """

        from heshly_core.models.knowledge import (
            BusinessProfile,
            FAQItem,
            BusinessPolicy,
        )

        faq_items = []
        for faq in self.faqs:
            if "|" in faq:
                question, answer = faq.split("|", 1)
                faq_items.append(
                    FAQItem(
                        question=question.strip(),
                        answer=answer.strip(),
                    )
                )
            else:
                faq_items.append(
                    FAQItem(
                        question=faq.strip(),
                        answer="",
                    )
                )

        policy_items = []
        for policy in self.policies:
            if "|" in policy:
                key, value = policy.split("|", 1)
                policy_items.append(
                    BusinessPolicy(
                        key=key.strip(),
                        value=value.strip(),
                    )
                )
            else:
                policy_items.append(
                    BusinessPolicy(
                        key=policy.strip(),
                        value="",
                    )
                )

        return KnowledgeContext(
            business=BusinessProfile(
                business_name=self.business_name,
                industry=self.industry,
                description=self.description,
            ),
            services=self.service_info(),
            products=list(self.products),
            faqs=faq_items,
            policies=policy_items,
        )
