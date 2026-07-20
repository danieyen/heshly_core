from heshly_core.models.system_prompt import (
    SystemPrompt,
)

from heshly_core.services.ai.system_prompt_manager import (
    SystemPromptManager,
)


def run_test():

    print("\n==============================")
    print("System Prompt Manager Test")
    print("==============================\n")

    manager = SystemPromptManager()

    prompt = SystemPrompt(

        prompt_id="prompt_001",

        tenant_id="tenant_001",

        name="Default Prompt",

        content=(
            "You are a professional "
            "AI receptionist."
        ),

    )

    manager.save(
        prompt
    )

    print("✅ Prompt saved")

    stored = manager.get(
        "tenant_001"
    )

    assert stored is not None

    print("✅ Prompt retrieved")

    manager.update(

        "tenant_001",

        "You are a friendly AI receptionist.",

    )

    updated = manager.get(
        "tenant_001"
    )

    assert updated is not None

    assert updated.version == 2

    print("✅ Prompt updated")

    assert updated.active

    print("✅ Prompt active")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check")

    print(
        "\n🎉 SYSTEM PROMPT MANAGER TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()