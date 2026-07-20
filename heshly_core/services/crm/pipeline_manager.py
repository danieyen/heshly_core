from __future__ import annotations

from heshly_core.models.crm import (
    Opportunity,
    PipelineStage,
)

from heshly_core.services.crm.pipeline_definition_manager import (
    PipelineDefinitionManager,
)

from heshly_core.services.crm.stage_manager import (
    StageManager,
)

from heshly_core.services.crm.stage_transition_manager import (
    StageTransitionManager,
)

from heshly_core.services.crm.pipeline_automation import (
    PipelineAutomationManager,
)

from heshly_core.services.crm.pipeline_metrics_manager import (
    PipelineMetricsManager,
)

from heshly_core.services.crm.pipeline_visualization import (
    PipelineVisualizationManager,
)



class PipelineManager:
    """
    Main Pipeline CRM controller.
    """


    def __init__(self):

        self.pipeline_creator = (
            PipelineDefinitionManager()
        )

        self.stage_manager = (
            StageManager()
        )

        self.transition_manager = (
            StageTransitionManager()
        )

        self.automation_manager = (
            PipelineAutomationManager()
        )

        self.metrics_manager = (
            PipelineMetricsManager()
        )

        self.visualization_manager = (
            PipelineVisualizationManager()
        )



    def create_pipeline(
        self,
        name: str,
        description: str | None = None,
        is_default: bool = False,
    ):

        return self.pipeline_creator.create_pipeline(
            name=name,
            description=description,
            is_default=is_default,
        )



    def add_stage(
        self,
        pipeline_id: str,
        name: str,
        order: int,
        probability: float,
    ):

        return self.stage_manager.create_stage(
            pipeline_id=pipeline_id,
            name=name,
            order=order,
            probability=probability,
        )



    def move_opportunity(
        self,
        opportunity: Opportunity,
        stage: PipelineStage,
    ):

        return self.stage_manager.create_stage(
            pipeline_id=stage.pipeline_id,
            name=stage.name,
            order=stage.order,
            probability=stage.probability,
        )



    def get_metrics(
        self,
        pipeline_id: str,
        opportunities: list[Opportunity],
    ):

        return self.metrics_manager.calculate(
            pipeline_id,
            opportunities,
        )



    def visualize(
        self,
        stages: list[PipelineStage],
        opportunities: list[Opportunity],
    ):

        return self.visualization_manager.build_view(
            stages,
            opportunities,
        )