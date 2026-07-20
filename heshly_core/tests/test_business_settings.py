from heshly_core.models.business_settings import (
    BusinessSettings,
    NotificationSettings,
    AISettings,
    IntegrationSettings,
)



def run_test():

    print("\n==============================")
    print("Business Settings Test")
    print("==============================\n")


    settings = BusinessSettings(

        business_id="business_001",

        timezone="Africa/Nairobi",

        currency="KES",

        language="en",

        notifications=NotificationSettings(

            whatsapp_enabled=True,

            reminders_enabled=True,

        ),

        ai=AISettings(

            enabled=True,

            personality="friendly",

        ),

        integrations=IntegrationSettings(

            calendar_enabled=True,

            crm_enabled=True,

        ),

    )


    assert settings.business_id == "business_001"


    print("✅ Settings creation passed")


    assert settings.timezone == "Africa/Nairobi"

    assert settings.currency == "KES"


    print("✅ Regional settings passed")


    assert settings.ai.enabled

    assert settings.ai.personality == "friendly"


    print("✅ AI settings passed")


    assert settings.integrations.calendar_enabled


    print("✅ Integration settings passed")


    settings.update_timezone(
        "UTC"
    )


    assert settings.timezone == "UTC"


    print("✅ Settings update passed")


    summary = settings.summary()


    assert summary["business_id"] == "business_001"


    print("✅ Summary passed")


    print("\n🎉 BUSINESS SETTINGS TEST PASSED\n")



if __name__ == "__main__":

    run_test()