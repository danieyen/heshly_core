from heshly_core.models.ai_profile import (

    AIProfile,

    AIPersonality,

    AITone,

)


def run_test():

    print("\n==============================")
    print("AI Profile Models Test")
    print("==============================\n")

    profile = AIProfile(

        profile_id="profile_001",

        tenant_id="tenant_001",

        name="Default Receptionist",

    )

    assert (

        profile.personality

        ==

        AIPersonality.RECEPTIONIST

    )

    print("✅ Default personality")

    assert (

        profile.tone

        ==

        AITone.PROFESSIONAL

    )

    print("✅ Default tone")

    profile.update(

        tone=AITone.FRIENDLY,

        greeting="Welcome to our clinic!",

    )

    assert (

        profile.tone

        ==

        AITone.FRIENDLY

    )

    print("✅ Profile update")

    assert (

        profile.greeting

        ==

        "Welcome to our clinic!"

    )

    print("✅ Greeting updated")

    print("\n🎉 AI PROFILE MODELS TEST PASSED\n")


if __name__ == "__main__":

    run_test()