from typing import Optional

from heshly_core.models.knowledge import (
    BusinessPolicy,
    KnowledgeContext,
)


class PolicyKnowledge:
    """
    Provides business policy knowledge.
    """

    def __init__(self, context: KnowledgeContext):
        self.context = context

    def all(self) -> list[BusinessPolicy]:
        return self.context.policies

    def keys(self) -> list[str]:
        return [policy.key for policy in self.context.policies]

    def find(self, key: str) -> Optional[BusinessPolicy]:
        key = key.lower()

        for policy in self.context.policies:
            if policy.key.lower() == key:
                return policy

        return None

    def value(self, key: str) -> Optional[str]:
        policy = self.find(key)

        if policy is None:
            return None

        return policy.value

    def exists(self, key: str) -> bool:
        return self.find(key) is not None