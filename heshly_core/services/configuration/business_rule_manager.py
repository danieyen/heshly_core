from __future__ import annotations

from heshly_core.models.business_rule import (
    BusinessRule,
)

from heshly_core.repositories.business_rule_repository import (
    BusinessRuleRepository,
)


class BusinessRuleManager:

    """
    Tenant Business Rule Manager.
    """

    def __init__(self):

        self.repository = BusinessRuleRepository()

    def save(
        self,
        rule: BusinessRule,
    ) -> BusinessRule:

        return self.repository.save(
            rule
        )

    def get(
        self,
        rule_id: str,
    ) -> BusinessRule | None:

        return self.repository.get(
            rule_id
        )

    def tenant_rules(
        self,
        tenant_id: str,
    ) -> list[BusinessRule]:

        return self.repository.for_tenant(
            tenant_id
        )

    def evaluate(
        self,
        tenant_id: str,
        condition: str,
    ) -> list[BusinessRule]:

        return [

            rule

            for rule in self.tenant_rules(
                tenant_id
            )

            if (
                rule.status.value == "active"
                and rule.condition == condition
            )

        ]

    def clear(self):

        self.repository.clear()

    def health(self):

        return {

            "service": "business_rule_manager",

            "status": "healthy",

        }