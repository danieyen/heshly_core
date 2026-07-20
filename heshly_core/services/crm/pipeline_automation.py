from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass(slots=True)
class PipelineAutomationRule:

    rule_id: str

    pipeline_id: str

    trigger_stage: str

    action: str

    enabled: bool = True

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )



@dataclass(slots=True)
class AutomationExecution:

    execution_id: str

    rule_id: str

    opportunity_id: str

    action: str

    executed_at: datetime = field(
        default_factory=datetime.utcnow
    )



class PipelineAutomationError(Exception):
    pass



class PipelineAutomationManager:
    """
    Manages pipeline automation rules.
    """


    def __init__(self):

        self.rules: list[
            PipelineAutomationRule
        ] = []

        self.executions: list[
            AutomationExecution
        ] = []



    def create_rule(
        self,
        pipeline_id: str,
        trigger_stage: str,
        action: str,
    ) -> PipelineAutomationRule:


        if not pipeline_id:

            raise PipelineAutomationError(
                "Pipeline ID is required."
            )


        if not trigger_stage:

            raise PipelineAutomationError(
                "Trigger stage is required."
            )


        if not action:

            raise PipelineAutomationError(
                "Automation action is required."
            )


        rule = PipelineAutomationRule(

            rule_id=self._generate_rule_id(),

            pipeline_id=pipeline_id,

            trigger_stage=trigger_stage,

            action=action,

        )


        self.rules.append(rule)

        return rule



    def execute(
        self,
        opportunity_id: str,
        stage_id: str,
    ) -> list[AutomationExecution]:


        executions = []


        for rule in self.rules:

            if (
                rule.enabled
                and rule.trigger_stage == stage_id
            ):


                execution = AutomationExecution(

                    execution_id=self._generate_execution_id(),

                    rule_id=rule.rule_id,

                    opportunity_id=opportunity_id,

                    action=rule.action,

                )


                self.executions.append(
                    execution
                )

                executions.append(
                    execution
                )


        return executions



    def _generate_rule_id(self):

        return (
            f"RULE-{uuid.uuid4().hex[:8].upper()}"
        )



    def _generate_execution_id(self):

        return (
            f"EXEC-{uuid.uuid4().hex[:8].upper()}"
        )