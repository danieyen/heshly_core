from heshly_core.services.business.business_onboarding import (
    BusinessOnboarding,
)

from heshly_core.services.business.business_manager import (
    BusinessManager,
)

from heshly_core.repositories.business_configuration_repository import (
    BusinessConfigurationRepository,
)

from heshly_core.models.business_profile import (
    BusinessProfile,
)

from heshly_core.models.business_settings import (
    BusinessSettings,
)



def run_test():

    print("\n================================")
    print("Business Account Final Integration Test")
    print("================================\n")


    # =====================================================
    # Load Services
    # =====================================================

    print("Loading Business Onboarding...")

    onboarding = BusinessOnboarding()

    print("✅ Business Onboarding loaded")


    print("Loading Business Manager...")

    manager = BusinessManager()

    print("✅ Business Manager loaded")


    print("Loading Configuration Storage...")

    configuration = BusinessConfigurationRepository()

    print("✅ Configuration Storage loaded")



    # =====================================================
    # Business Onboarding
    # =====================================================

    print("\nTesting business onboarding...")


    business = onboarding.onboard(

        business_id="business_001",

        tenant_id="tenant_001",

        name="Acme Dental Clinic",

        industry="Dental",

        location="Nairobi",

        email="admin@acme.com",

        phone="+254700000001",

    )


    assert business is not None

    assert business.name == "Acme Dental Clinic"


    print("✅ Business onboarding passed")



    # =====================================================
    # Profile
    # =====================================================

    print("\nTesting business profile...")


    assert business.profile is not None

    assert (
        business.profile.industry
        ==
        "Dental"
    )


    print("✅ Business profile passed")



    # =====================================================
    # Settings
    # =====================================================

    print("\nTesting business settings...")


    assert business.settings is not None

    assert (
        business.settings.currency
        ==
        "KES"
    )


    print("✅ Business settings passed")



    # =====================================================
    # Repository Retrieval
    # =====================================================

    print("\nTesting business retrieval...")


    stored = manager.get(
        "business_001"
    )


    assert stored is not None

    assert (
        stored.tenant_id
        ==
        "tenant_001"
    )


    print("✅ Business repository retrieval passed")



    # =====================================================
    # Configuration Storage
    # =====================================================

    print("\nTesting configuration storage...")


    profile = BusinessProfile(

        business_id="business_001",

        name="Acme Dental Clinic",

        industry="Healthcare",

    )


    settings = BusinessSettings(

        business_id="business_001",

        currency="KES",

    )


    configuration.save_profile(
        profile
    )


    configuration.save_settings(
        settings
    )


    config = configuration.get_configuration(
        "business_001"
    )


    assert config["profile"] is not None

    assert config["settings"] is not None


    print("✅ Configuration storage passed")



    # =====================================================
    # Lifecycle
    # =====================================================

    print("\nTesting business lifecycle...")


    manager.suspend(
        "business_001"
    )


    suspended = manager.get(
        "business_001"
    )


    assert suspended.status == "suspended"


    print("✅ Suspension passed")



    manager.activate(
        "business_001"
    )


    active = manager.get(
        "business_001"
    )


    assert active.is_active


    print("✅ Activation passed")



    # =====================================================
    # Health Checks
    # =====================================================

    print("\nTesting health checks...")


    assert (
        onboarding.health()["status"]
        ==
        "healthy"
    )


    assert (
        manager.health()["status"]
        ==
        "healthy"
    )


    assert (
        configuration.health()["status"]
        ==
        "healthy"
    )


    print("✅ Health checks passed")



    print(
        "\n🎉 BUSINESS ACCOUNT FINAL INTEGRATION TEST PASSED\n"
    )



if __name__ == "__main__":

    run_test()