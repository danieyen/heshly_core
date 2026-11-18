from heshly_core.services.business.business_onboarding import (
    BusinessOnboarding,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)


def run_test():

    print("\n========================================")
    print("Business Onboarding / Frappe Test")
    print("========================================\n")

    context = TenantContext()
    onboarding = BusinessOnboarding()

    # =====================================================
    # Tenant Context
    # =====================================================

    context.set("heshly")

    print("context:", context.get())

    # =====================================================
    # Onboard Business
    # =====================================================

    business = onboarding.onboard(
        business_id="ONBOARD_TEST_001",
        name="Acme Dental Clinic",
        domain="acme-dental.example.com",
        industry="Dental",
        location="Nairobi",
        email="admin@acme.com",
        phone="+254700000001",
    )

    print("business:", business)

    assert business is not None
    assert business.business_id == "ONBOARD_TEST_001"
    assert business.tenant_id == "heshly"
    assert business.name == "Acme Dental Clinic"

    print("✅ Business identity passed")

    # =====================================================
    # Profile
    # =====================================================

    assert business.profile.industry == "Dental"
    assert business.profile.location == "Nairobi"

    print("✅ Profile setup passed")

    # =====================================================
    # Settings
    # =====================================================

    assert business.settings.currency == "KES"
    assert business.settings.timezone == "Africa/Nairobi"

    print("✅ Default settings passed")

    # =====================================================
    # Lifecycle
    # =====================================================

    assert business.is_active

    print("✅ Activation passed")

    # =====================================================
    # Persistence
    # =====================================================

    reloaded = onboarding.manager.get(
        "ONBOARD_TEST_001"
    )

    assert reloaded is not None
    assert reloaded.business_id == "ONBOARD_TEST_001"
    assert reloaded.tenant_id == "heshly"
    assert reloaded.profile.industry == "Dental"
    assert reloaded.settings.currency == "KES"

    print("✅ Frappe persistence passed")

    # =====================================================
    # Tenant Isolation
    # =====================================================

    context.set("tenant_other")

    hidden = onboarding.manager.get(
        "ONBOARD_TEST_001"
    )

    assert hidden is None

    print("✅ Tenant isolation passed")

    # =====================================================
    # Restore Tenant
    # =====================================================

    context.set("heshly")

    visible = onboarding.manager.get(
        "ONBOARD_TEST_001"
    )

    assert visible is not None

    print("✅ Tenant restoration passed")

    # =====================================================
    # Missing Context
    # =====================================================

    context.clear()

    try:
        onboarding.onboard(
            business_id="ONBOARD_TEST_002",
            name="Should Fail",
            domain="should-fail.example.com",
        )
    except RuntimeError as e:
        print("missing context:", e)
    else:
        raise AssertionError(
            "Expected RuntimeError when tenant context is missing"
        )

    print("✅ Tenant context requirement passed")

    # =====================================================
    # Health
    # =====================================================

    context.set("heshly")

    health = onboarding.health()

    print("health:", health)

    assert health["status"] == "healthy"
    assert health["tenant"] is True

    print("✅ Onboarding health passed")

    # =====================================================
    # Cleanup
    # =====================================================

    context.clear()

    print()
    print("🎉 BUSINESS ONBOARDING / FRAPPE TEST PASSED")


if __name__ == "__main__":
    run_test()
