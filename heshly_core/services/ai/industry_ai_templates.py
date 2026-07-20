from __future__ import annotations

from heshly_core.models.ai_profile import (
    AIProfile,
    AIPersonality,
    AITone,
)


class IndustryAITemplates:
    """
    Industry AI Templates.

    Provides default AI profiles
    for supported industries.
    """

    def dental(self) -> AIProfile:

        return AIProfile(

            profile_id="template_dental",

            tenant_id="template",

            name="Dental Receptionist",

            personality=AIPersonality.RECEPTIONIST,

            tone=AITone.PROFESSIONAL,

            greeting=(
                "Welcome to our dental clinic. "
                "How may I assist you today?"
            ),

            farewell=(
                "Thank you for choosing our clinic."
            ),

        )

    def salon(self) -> AIProfile:

        return AIProfile(

            profile_id="template_salon",

            tenant_id="template",

            name="Salon Receptionist",

            personality=AIPersonality.RECEPTIONIST,

            tone=AITone.FRIENDLY,

            greeting=(
                "Welcome! Ready for a great look today?"
            ),

            farewell="See you again soon!",

        )

    def logistics(self) -> AIProfile:

        return AIProfile(

            profile_id="template_logistics",

            tenant_id="template",

            name="Logistics Assistant",

            personality=AIPersonality.CUSTOMER_SUPPORT,

            tone=AITone.PROFESSIONAL,

            greeting=(
                "Welcome to our logistics support desk."
            ),

            farewell="Thank you for shipping with us.",

        )

    def insurance(self) -> AIProfile:

        return AIProfile(

            profile_id="template_insurance",

            tenant_id="template",

            name="Insurance Advisor",

            personality=AIPersonality.SALES,

            tone=AITone.FORMAL,

            greeting=(
                "Welcome. How may we assist "
                "with your insurance needs?"
            ),

            farewell=(
                "Thank you for choosing our services."
            ),

        )

    def real_estate(self) -> AIProfile:

        return AIProfile(

            profile_id="template_real_estate",

            tenant_id="template",

            name="Property Assistant",

            personality=AIPersonality.SALES,

            tone=AITone.FRIENDLY,

            greeting=(
                "Welcome! Let's find your ideal property."
            ),

            farewell=(
                "We look forward to helping you."
            ),

        )

    # =====================================================
    # Factory
    # =====================================================

    def load(
        self,
        industry: str,
    ) -> AIProfile:

        templates = {

            "dental": self.dental,

            "salon": self.salon,

            "logistics": self.logistics,

            "insurance": self.insurance,

            "real_estate": self.real_estate,

        }

        loader = templates.get(
            industry.lower()
        )

        if loader is None:

            raise ValueError(
                f"Unknown industry: {industry}"
            )

        return loader()