from heshly_core.services.ai.ai_personality_manager import (
    AIPersonalityManager,
)


def run_test():

    print("\n==============================")
    print("AI Personality Manager Test")
    print("==============================\n")

    manager = AIPersonalityManager()

    manager.update(

        tenant_id="tenant_001",

        friendliness=9,

        empathy=8,

        emoji_usage=True,

        allow_small_talk=True,

    )

    settings = manager.get(
        "tenant_001"
    )

    assert settings is not None

    print("✅ Settings created")

    assert settings.friendliness == 9

    print("✅ Friendliness updated")

    assert settings.empathy == 8

    print("✅ Empathy updated")

    assert settings.emoji_usage

    print("✅ Emoji preference updated")

    assert settings.allow_small_talk

    print("✅ Small talk enabled")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check")

    print("\n🎉 AI PERSONALITY SETTINGS TEST PASSED\n")


if __name__ == "__main__":

    run_test()