from heshly_core.models.business_profile import (
    BusinessProfile,
)


def run_test():

    print("\n==============================")
    print("Business Profile Test")
    print("==============================\n")


    profile = BusinessProfile(

        business_id="business_001",

        name="Acme Dental Clinic",

        industry="Dental",

        location="Nairobi",

        email="admin@acme.com",

        phone="+254700000001",

    )


    assert profile.name == "Acme Dental Clinic"

    assert profile.industry == "Dental"

    assert profile.location == "Nairobi"


    print("✅ Business identity passed")


    assert profile.email == "admin@acme.com"

    assert profile.phone == "+254700000001"


    print("✅ Contact details passed")


    profile.update_contact(

        phone="+254711111111",

        website="https://acme.com",

    )


    assert profile.phone == "+254711111111"

    assert profile.website == "https://acme.com"


    print("✅ Contact update passed")


    profile.update_location(
        "Mombasa"
    )


    assert profile.location == "Mombasa"


    print("✅ Location update passed")


    summary = profile.summary()


    assert summary["name"] == "Acme Dental Clinic"


    print("✅ Summary passed")


    print("\n🎉 BUSINESS PROFILE TEST PASSED\n")



if __name__ == "__main__":

    run_test()