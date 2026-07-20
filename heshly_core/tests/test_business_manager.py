from heshly_core.models.business_account import (
    BusinessAccount,
)

from heshly_core.models.business_profile import (
    BusinessProfile,
)

from heshly_core.models.business_settings import (
    BusinessSettings,
)

from heshly_core.services.business.business_manager import (
    BusinessManager,
)



def run_test():

    print("\n==============================")
    print("Business Manager Test")
    print("==============================\n")


    manager = BusinessManager()


    business = BusinessAccount(

        business_id="business_001",

        tenant_id="tenant_001",

        name="Acme Dental",

    )


    manager.create(
        business
    )


    print("✅ Business creation passed")



    result = manager.get(
        "business_001"
    )


    assert result is not None

    assert result.name == "Acme Dental"


    print("✅ Business retrieval passed")



    profile = BusinessProfile(

        business_id="business_001",

        name="Acme Dental",

        industry="Dental",

    )


    manager.update_profile(

        "business_001",

        profile,

    )


    assert (
        manager.get(
            "business_001"
        ).profile.industry
        ==
        "Dental"
    )


    print("✅ Profile update passed")



    settings = BusinessSettings(

        business_id="business_001"

    )


    manager.update_settings(

        "business_001",

        settings,

    )


    print("✅ Settings update passed")



    manager.suspend(
        "business_001"
    )


    assert (
        manager.get(
            "business_001"
        ).status
        ==
        "suspended"
    )


    print("✅ Suspension passed")



    manager.activate(
        "business_001"
    )


    assert (
        manager.get(
            "business_001"
        ).is_active
    )


    print("✅ Activation passed")



    print("\n🎉 BUSINESS MANAGER TEST PASSED\n")



if __name__ == "__main__":

    run_test()