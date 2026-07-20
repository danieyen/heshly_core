from __future__ import annotations

from heshly_core.models.ai_personality_settings import (
    AIPersonalitySettings,
)


class AIPersonalityRepository:

    def __init__(self):

        self._storage: dict[
            str,
            AIPersonalitySettings,
        ] = {}

    def save(
        self,
        settings: AIPersonalitySettings,
    ) -> AIPersonalitySettings:

        self._storage[
            settings.tenant_id
        ] = settings

        return settings

    def get(
        self,
        tenant_id: str,
    ) -> AIPersonalitySettings | None:

        return self._storage.get(
            tenant_id
        )

    def exists(
        self,
        tenant_id: str,
    ) -> bool:

        return tenant_id in self._storage

    def delete(
        self,
        tenant_id: str,
    ) -> bool:

        return self._storage.pop(
            tenant_id,
            None,
        ) is not None

    def clear(self):

        self._storage.clear()