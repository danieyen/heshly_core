from __future__ import annotations

from heshly_core.models.ai_profile import AIProfile
from heshly_core.models.business_knowledge_profile import (
    BusinessKnowledgeProfile,
)
from heshly_core.models.system_prompt import SystemPrompt

from heshly_core.services.ai.ai_personality_manager import (
    AIPersonalityManager,
)
from heshly_core.services.ai.industry_ai_templates import (
    IndustryAITemplates,
)
from heshly_core.services.ai.system_prompt_manager import (
    SystemPromptManager,
)


class TenantAIManager:
    """
    Tenant AI Manager.

    Central manager responsible for
    tenant-specific AI customization.
    """

    def __init__(self):

        self.templates = IndustryAITemplates()

        self.prompt_manager = SystemPromptManager()

        self.personality_manager = (
            AIPersonalityManager()
        )

        self._profiles: dict[str, AIProfile] = {}

        self._knowledge: dict[
            str,
            BusinessKnowledgeProfile,
        ] = {}

    # =====================================================
    # AI Profile
    # =====================================================

    def save_profile(
        self,
        profile: AIProfile,
    ):

        self._profiles[
            profile.tenant_id
        ] = profile

        return profile

    def profile(
        self,
        tenant_id: str,
    ) -> AIProfile | None:

        return self._profiles.get(
            tenant_id
        )

    # =====================================================
    # Knowledge Profile
    # =====================================================

    def save_knowledge(
        self,
        knowledge: BusinessKnowledgeProfile,
    ):

        self._knowledge[
            knowledge.tenant_id
        ] = knowledge

        return knowledge

    def knowledge(
        self,
        tenant_id: str,
    ) -> BusinessKnowledgeProfile | None:

        return self._knowledge.get(
            tenant_id
        )

    # =====================================================
    # System Prompt
    # =====================================================

    def prompt(
        self,
        tenant_id: str,
    ) -> SystemPrompt | None:

        return self.prompt_manager.get(
            tenant_id
        )

    # =====================================================
    # Personality
    # =====================================================

    def personality(
        self,
        tenant_id: str,
    ):

        return self.personality_manager.get(
            tenant_id
        )

    # =====================================================
    # Industry Templates
    # =====================================================

    def apply_template(
        self,
        tenant_id: str,
        industry: str,
    ) -> AIProfile:

        profile = self.templates.load(
            industry
        )

        profile.tenant_id = tenant_id

        self.save_profile(
            profile
        )

        return profile

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        tenant_id: str,
    ) -> dict:

        return {

            "profile": self.profile(
                tenant_id
            ),

            "knowledge": self.knowledge(
                tenant_id
            ),

            "prompt": self.prompt(
                tenant_id
            ),

            "personality": self.personality(
                tenant_id
            ),

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "tenant_ai_manager",

            "status": "healthy",

        }