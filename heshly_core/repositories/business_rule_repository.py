from __future__ import annotations

from heshly_core.models.business_rule import (
    BusinessRule,
)


class BusinessRuleRepository:

    def __init__(self):

        self._rules: dict[str, BusinessRule] = {}

    def save(
        self,
        rule: BusinessRule,
    ) -> BusinessRule:

        self._rules[rule.rule_id] = rule

        return rule

    def get(
        self,
        rule_id: str,
    ) -> BusinessRule | None:

        return self._rules.get(rule_id)

    def all(self) -> list[BusinessRule]:

        return list(
            self._rules.values()
        )

    def for_tenant(
        self,
        tenant_id: str,
    ) -> list[BusinessRule]:

        return [

            rule

            for rule in self._rules.values()

            if rule.tenant_id == tenant_id

        ]

    def delete(
        self,
        rule_id: str,
    ) -> bool:

        if rule_id not in self._rules:

            return False

        del self._rules[rule_id]

        return True

    def clear(self):

        self._rules.clear()