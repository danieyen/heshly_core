from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class WorkflowStep:

    step_id: str

    name: str

    action: str

    order: int

    enabled: bool = True


@dataclass(slots=True)
class WorkflowTemplate:
    """
    Tenant Workflow Template.
    """

    template_id: str

    name: str

    industry: str

    description: str = ""

    steps: list[WorkflowStep] = field(
        default_factory=list
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def add_step(
        self,
        step: WorkflowStep,
    ):

        self.steps.append(step)

        self.steps.sort(
            key=lambda s: s.order
        )

        self.updated_at = datetime.now(UTC)

    @property
    def step_count(self) -> int:

        return len(self.steps)