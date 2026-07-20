from heshly_core.models.business_profile import (
    BusinessProfile,
)

from heshly_core.models.business_settings import (
    BusinessSettings,
)

from heshly_core.repositories.business_configuration_repository import (
    BusinessConfigurationRepository,
)



def run_test():

    print("\n==============================")
    print("Business Configuration Storage Test")
    print("==============================\n")


    repository = BusinessConfigurationRepository()



    profile = BusinessProfile(

        business_id="business_001",

        name="Acme Dental",

        industry="Healthcare",

        location="Nairobi",

    )


    repository.save_profile(
        profile
    )


    result = repository.get_profile(
        "business_001"
    )


    assert result.name == "Acme Dental"


    print("✅ Profile storage passed")



    settings = BusinessSettings(

        business_id="business_001",

        currency="KES",

        timezone="Africa/Nairobi",

    )


    repository.save_settings(
        settings
    )


    result = repository.get_settings(
        "business_001"
    )


    assert result.currency == "KES"


    print("✅ Settings storage passed")



    configuration = repository.get_configuration(
        "business_001"
    )


    assert (
        configuration["profile"]
        is not None
    )


    assert (
        configuration["settings"]
        is not None
    )


    print("✅ Combined configuration retrieval passed")



    repository.delete(
        "business_001"
    )


    assert (
        repository.get_profile(
            "business_001"
        )
        is None
    )


    print("✅ Configuration deletion passed")



    print("\n🎉 BUSINESS CONFIGURATION STORAGE TEST PASSED\n")



if __name__ == "__main__":

    run_test()