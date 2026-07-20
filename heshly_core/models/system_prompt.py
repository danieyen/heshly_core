from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class SystemPrompt:
    """
    Tenant System Prompt.
    """

    prompt_id: str

    tenant_id: str

    name: str

    content: str

    version: int = 1

    active: bool = True

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def update(
        self,
        content: str,
    ):

        self.content = content

        self.version += 1

        self.updated_at = datetime.now(UTC)

    def activate(self):

        self.active = True

        self.updated_at = datetime.now(UTC)

    def deactivate(self):

        self.active = False

        self.updated_at = datetime.now(UTC)