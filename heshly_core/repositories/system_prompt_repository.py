from __future__ import annotations

from heshly_core.models.system_prompt import (
    SystemPrompt,
)


class SystemPromptRepository:

    def __init__(self):

        self._prompts: dict[
            str,
            SystemPrompt,
        ] = {}

    def save(
        self,
        prompt: SystemPrompt,
    ) -> SystemPrompt:

        self._prompts[
            prompt.tenant_id
        ] = prompt

        return prompt

    def get(
        self,
        tenant_id: str,
    ) -> SystemPrompt | None:

        return self._prompts.get(
            tenant_id
        )

    def exists(
        self,
        tenant_id: str,
    ) -> bool:

        return tenant_id in self._prompts

    def delete(
        self,
        tenant_id: str,
    ) -> bool:

        return self._prompts.pop(
            tenant_id,
            None,
        ) is not None

    def clear(self):

        self._prompts.clear()