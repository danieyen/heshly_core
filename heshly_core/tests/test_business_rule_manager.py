from heshly_core.models.business_rule import (
    BusinessRule,
)

from heshly_core.services.configuration.business_rule_manager import (
    BusinessRuleManager,
)


def run_test():

    print("\n==============================")
    print("Business Rule Manager Test")
    print("==============================\n")

    manager = BusinessRuleManager()

    rule = BusinessRule(

        rule_id="rule_001",

        tenant_id="tenant_001",

        name="Premium Lead",

        condition="lead_score>80",

        action="assign_senior_agent",

    )

    manager.save(
        rule
    )

    print("✅ Rule saved")

    stored = manager.get(
        "rule_001"
    )

    assert stored is not None

    print("✅ Rule retrieved")

    rules = manager.tenant_rules(
        "tenant_001"
    )

    assert len(rules) == 1

    print("✅ Tenant rule lookup")

    matched = manager.evaluate(

        "tenant_001",

        "lead_score>80",

    )

    assert len(matched) == 1

    print("✅ Rule evaluation")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check")

    print("\n🎉 BUSINESS RULE MANAGER TEST PASSED\n")


if __name__ == "__main__":

    run_test()