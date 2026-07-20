from heshly_core.services.configuration.configuration_manager import (
    ConfigurationManager,
)

from heshly_core.services.configuration.industry_templates import (
    IndustryTemplates,
)

from heshly_core.services.configuration.business_rule_manager import (
    BusinessRuleManager,
)

from heshly_core.services.configuration.tenant_preferences_manager import (
    TenantPreferencesManager,
)

from heshly_core.models.business_rule import (
    BusinessRule,
)


def run_test():

    print("\n====================================")
    print("Configuration Integration Test")
    print("====================================\n")

    # =====================================================
    # Configuration Manager
    # =====================================================

    print("Loading Configuration Manager...")

    manager = ConfigurationManager()

    print("✅ Configuration Manager loaded")

    # =====================================================
    # Industry Templates
    # =====================================================

    print("Loading Industry Templates...")

    templates = IndustryTemplates()

    print("✅ Industry Templates loaded")

    # =====================================================
    # Business Rules
    # =====================================================

    print("Loading Business Rule Manager...")

    rules = BusinessRuleManager()

    print("✅ Business Rule Manager loaded")

    # =====================================================
    # Preferences
    # =====================================================

    print("Loading Tenant Preferences...")

    preferences = TenantPreferencesManager()

    print("✅ Tenant Preferences loaded")

    # =====================================================
    # Configuration
    # =====================================================

    print("\nTesting configuration...")

    manager.set(

        tenant_id="tenant_001",

        key="timezone",

        value="Africa/Nairobi",

    )

    assert (

        manager.value(

            "tenant_001",

            "timezone",

        )

        ==

        "Africa/Nairobi"

    )

    print("✅ Configuration passed")

    # =====================================================
    # Industry Template
    # =====================================================

    print("\nTesting industry template...")

    dental = templates.load(
        "dental"
    )

    assert (

        dental.get("industry")

        ==

        "Dental Clinic"

    )

    print("✅ Industry template passed")

    # =====================================================
    # Business Rules
    # =====================================================

    print("\nTesting business rules...")

    rule = BusinessRule(

        rule_id="rule_001",

        tenant_id="tenant_001",

        name="Premium Leads",

        condition="lead_score>80",

        action="assign_manager",

    )

    rules.save(rule)

    matched = rules.evaluate(

        "tenant_001",

        "lead_score>80",

    )

    assert len(matched) == 1

    print("✅ Business rules passed")

    # =====================================================
    # Preferences
    # =====================================================

    print("\nTesting preferences...")

    preferences.update(

        tenant_id="tenant_001",

        language="en",

        timezone="Africa/Nairobi",

        currency="KES",

        theme="dark",

    )

    pref = preferences.get(
        "tenant_001"
    )

    assert pref is not None

    assert pref.currency == "KES"

    print("✅ Preferences passed")

    # =====================================================
    # Health
    # =====================================================

    print("\nTesting health...")

    assert (

        manager.health()["status"]

        ==

        "healthy"

    )

    assert (

        rules.health()["status"]

        ==

        "healthy"

    )

    assert (

        preferences.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health checks passed")

    print("\n====================================")
    print("🎉 CONFIGURATION ENGINE PASSED")
    print("====================================\n")


if __name__ == "__main__":

    run_test()