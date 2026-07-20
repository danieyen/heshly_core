from __future__ import annotations

from heshly_core.models.ai_personality_settings import (
    AIPersonalitySettings,
)

from heshly_core.repositories.ai_personality_repository import (
    AIPersonalityRepository,
)


class AIPersonalityManager:

    """
    AI Personality Manager.
    """

    def __init__(self):

        self.repository = (
            AIPersonalityRepository()
        )

    def create(
        self,
        tenant_id: str,
    ) -> AIPersonalitySettings:

        settings = AIPersonalitySettings(
            tenant_id=tenant_id
        )

        self.repository.save(
            settings
        )

        return settings

    def get(
        self,
        tenant_id: str,
    ) -> AIPersonalitySettings | None:

        return self.repository.get(
            tenant_id
        )

    def get_or_create(
        self,
        tenant_id: str,
    ) -> AIPersonalitySettings:

        settings = self.get(
            tenant_id
        )

        if settings is None:

            settings = self.create(
                tenant_id
            )

        return settings

    def update(
        self,
        tenant_id: str,
        **kwargs,
    ) -> AIPersonalitySettings:

        settings = self.get_or_create(
            tenant_id
        )

        settings.update(
            **kwargs
        )

        self.repository.save(
            settings
        )

        return settings

    def health(self):

        return {

            "service": "ai_personality_manager",

            "status": "healthy",

        }