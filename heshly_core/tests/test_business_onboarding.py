from heshly_core.services.business.business_onboarding import (
    BusinessOnboarding,
)



def run_test():

    print("\n==============================")
    print("Business Onboarding Test")
    print("==============================\n")


    onboarding = BusinessOnboarding()



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


    print("✅ Business creation passed")



    assert business.name == "Acme Dental Clinic"


    print("✅ Business identity passed")



    assert business.profile.industry == "Dental"


    print("✅ Profile setup passed")



    assert business.settings.currency == "KES"


    print("✅ Default settings passed")



    assert business.is_active


    print("✅ Activation passed")



    print("\n🎉 BUSINESS ONBOARDING TEST PASSED\n")



if __name__ == "__main__":

    run_test()