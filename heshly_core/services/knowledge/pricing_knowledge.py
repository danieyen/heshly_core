from typing import Optional

from heshly_core.models.knowledge import (
    KnowledgeContext,
    ServiceInfo,
)


class PricingKnowledge:
    """
    Provides pricing-related business knowledge.
    """

    def __init__(self, context: KnowledgeContext):
        self.context = context

    def all(self) -> dict[str, float]:
        prices = {}

        for service in self.context.services:
            if service.price is not None:
                prices[service.name] = service.price

        return prices

    def price(self, service_name: str) -> Optional[float]:
        for service in self.context.services:
            if service.name.lower() == service_name.lower():
                return service.price

        return None

    def has_price(self, service_name: str) -> bool:
        return self.price(service_name) is not None

    def cheapest(self) -> Optional[ServiceInfo]:
        priced = [
            service
            for service in self.context.services
            if service.price is not None
        ]

        if not priced:
            return None

        return min(priced, key=lambda service: service.price)

    def most_expensive(self) -> Optional[ServiceInfo]:
        priced = [
            service
            for service in self.context.services
            if service.price is not None
        ]

        if not priced:
            return None

        return max(priced, key=lambda service: service.price)