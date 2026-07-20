from __future__ import annotations

from heshly_core.models.system_prompt import (
    SystemPrompt,
)

from heshly_core.repositories.system_prompt_repository import (
    SystemPromptRepository,
)


class SystemPromptManager:

    """
    Tenant System Prompt Manager.
    """

    def __init__(self):

        self.repository = (
            SystemPromptRepository()
        )

    def save(
        self,
        prompt: SystemPrompt,
    ) -> SystemPrompt:

        return self.repository.save(
            prompt
        )

    def get(
        self,
        tenant_id: str,
    ) -> SystemPrompt | None:

        return self.repository.get(
            tenant_id
        )

    def update(
        self,
        tenant_id: str,
        content: str,
    ) -> SystemPrompt:

        prompt = self.repository.get(
            tenant_id
        )

        if prompt is None:

            raise ValueError(
                "System prompt not found."
            )

        prompt.update(content)

        self.repository.save(prompt)

        return prompt

    def health(self):

        return {

            "service": "system_prompt_manager",

            "status": "healthy",

        }