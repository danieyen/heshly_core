from heshly_core.models.business_account import (
    BusinessAccount,
    BusinessProfile,
    BusinessSettings,
    BusinessAccountStatus,
)



def run_test():

    print("\n==============================")
    print("Business Account Model Test")
    print("==============================\n")


    business = BusinessAccount(

        business_id="business_001",

        tenant_id="tenant_001",

        name="Acme Dental Clinic",

        domain="acme.example.com",

        email="admin@acme.com",

        profile=BusinessProfile(

            industry="Dental",

            location="Nairobi",

        ),

        settings=BusinessSettings(

            currency="KES",

        ),

    )


    assert business.business_id == "business_001"

    assert business.tenant_id == "tenant_001"

    assert business.name == "Acme Dental Clinic"


    print("✅ Business account creation passed")



    assert business.is_active


    print("✅ Default active status passed")



    business.suspend()


    assert (
        business.status
        ==
        BusinessAccountStatus.SUSPENDED
    )


    print("✅ Suspend business passed")



    business.activate()


    assert business.is_active


    print("✅ Activate business passed")



    business.deactivate()


    assert (
        business.status
        ==
        BusinessAccountStatus.INACTIVE
    )


    print("✅ Deactivate business passed")



    print("\n🎉 BUSINESS ACCOUNT MODEL TEST PASSED\n")



if __name__ == "__main__":

    run_test()