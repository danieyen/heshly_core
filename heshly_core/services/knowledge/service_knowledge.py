from typing import Optional

from heshly_core.models.knowledge import (
    KnowledgeContext,
    ServiceInfo,
)


class ServiceKnowledge:
    """
    Provides service-related business knowledge.
    """

    def __init__(self, context: KnowledgeContext):
        self.context = context

    def all(self) -> list[ServiceInfo]:
        return self.context.services

    def names(self) -> list[str]:
        return [service.name for service in self.context.services]

    def find(self, name: str) -> Optional[ServiceInfo]:
        for service in self.context.services:
            if service.name.lower() == name.lower():
                return service
        return None

    def exists(self, name: str) -> bool:
        return self.find(name) is not None