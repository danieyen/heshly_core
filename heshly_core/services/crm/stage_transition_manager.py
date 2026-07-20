from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass(slots=True)
class StageTransitionRule:

    rule_id: str

    pipeline_id: str

    from_stage: str

    to_stage: str

    allowed: bool = True

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )



class StageTransitionError(Exception):
    pass



class StageTransitionManager:
    """
    Manages allowed pipeline stage movements.
    """


    def __init__(self):

        self.rules: list[
            StageTransitionRule
        ] = []



    def create_rule(
        self,
        pipeline_id: str,
        from_stage: str,
        to_stage: str,
    ) -> StageTransitionRule:


        if not pipeline_id:

            raise StageTransitionError(
                "Pipeline ID is required."
            )


        if not from_stage:

            raise StageTransitionError(
                "Source stage is required."
            )


        if not to_stage:

            raise StageTransitionError(
                "Destination stage is required."
            )


        rule = StageTransitionRule(

            rule_id=self._generate_id(),

            pipeline_id=pipeline_id,

            from_stage=from_stage,

            to_stage=to_stage,

        )


        self.rules.append(rule)


        return rule



    def can_transition(
        self,
        pipeline_id: str,
        from_stage: str,
        to_stage: str,
    ) -> bool:


        for rule in self.rules:

            if (
                rule.pipeline_id == pipeline_id
                and rule.from_stage == from_stage
                and rule.to_stage == to_stage
                and rule.allowed
            ):

                return True


        return False



    def validate_transition(
        self,
        pipeline_id: str,
        from_stage: str,
        to_stage: str,
    ):


        if not self.can_transition(
            pipeline_id,
            from_stage,
            to_stage,
        ):

            raise StageTransitionError(
                f"Transition not allowed: "
                f"{from_stage} → {to_stage}"
            )


        return True



    def _generate_id(self):

        return (
            f"TRANS-{uuid.uuid4().hex[:8].upper()}"
        )