from heshly_core.models.business_knowledge_profile import (
    BusinessKnowledgeProfile,
)
from heshly_core.models.system_prompt import (
    SystemPrompt,
)
from heshly_core.services.ai.system_prompt_manager import (
    SystemPromptManager,
)
from heshly_core.services.ai.ai_personality_manager import (
    AIPersonalityManager,
)
from heshly_core.services.ai.tenant_ai_manager import (
    TenantAIManager,
)


def run_test():

    print("\n================================")
    print("Tenant AI Manager Test")
    print("================================\n")

    manager = TenantAIManager()

    # ---------------------------------
    # Apply industry template
    # ---------------------------------

    profile = manager.apply_template(

        tenant_id="tenant_001",

        industry="dental",

    )

    assert profile.name == "Dental Receptionist"

    print("✅ Industry template applied")

    # ---------------------------------
    # Knowledge
    # ---------------------------------

    knowledge = BusinessKnowledgeProfile(

        profile_id="knowledge_001",

        tenant_id="tenant_001",

        business_name="Smile Dental",

        industry="Dental",

    )

    manager.save_knowledge(
        knowledge
    )

    assert manager.knowledge(
        "tenant_001"
    ) is not None

    print("✅ Knowledge profile")

    # ---------------------------------
    # Prompt
    # ---------------------------------

    prompt_manager = SystemPromptManager()

    prompt_manager.save(

        SystemPrompt(

            prompt_id="prompt_001",

            tenant_id="tenant_001",

            name="Default",

            content="You are a helpful AI.",

        )

    )

    manager.prompt_manager = prompt_manager

    assert manager.prompt(
        "tenant_001"
    ) is not None

    print("✅ System prompt")

    # ---------------------------------
    # Personality
    # ---------------------------------

    personality_manager = AIPersonalityManager()

    personality_manager.update(

        tenant_id="tenant_001",

        friendliness=9,

    )

    manager.personality_manager = personality_manager

    assert manager.personality(
        "tenant_001"
    ) is not None

    print("✅ Personality settings")

    # ---------------------------------
    # Summary
    # ---------------------------------

    summary = manager.summary(
        "tenant_001"
    )

    assert summary["profile"] is not None

    print("✅ Summary")

    assert manager.health()["status"] == "healthy"

    print("✅ Health check")

    print("\n🎉 TENANT AI MANAGER TEST PASSED\n")


if __name__ == "__main__":

    run_test()