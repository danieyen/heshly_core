from heshly_core.models.business_knowledge_profile import (
    BusinessKnowledgeProfile,
)


def run_test():

    print("\n==============================")
    print("Business Knowledge Profile Test")
    print("==============================\n")

    profile = BusinessKnowledgeProfile(

        profile_id="knowledge_001",

        tenant_id="tenant_001",

        business_name="Smile Dental Clinic",

        industry="Dental",

    )

    print("✅ Profile created")

    profile.add_service(
        "Dental Cleaning"
    )

    profile.add_service(
        "Root Canal"
    )

    assert len(profile.services) == 2

    print("✅ Services added")

    profile.add_product(
        "Toothbrush"
    )

    assert len(profile.products) == 1

    print("✅ Products added")

    profile.add_faq(
        "Do you accept insurance?"
    )

    assert len(profile.faqs) == 1

    print("✅ FAQ added")

    profile.add_policy(
        "24-hour cancellation policy"
    )

    assert len(profile.policies) == 1

    print("✅ Policy added")

    print("\n🎉 BUSINESS KNOWLEDGE PROFILE TEST PASSED\n")


if __name__ == "__main__":

    run_test()