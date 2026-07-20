from __future__ import annotations

import uuid
from datetime import datetime

from heshly_core.models.crm import PipelineStage


class StageManagementError(Exception):
    pass



class StageManager:
    """
    Manages pipeline stages.
    """


    def __init__(self):

        self.stages: list[PipelineStage] = []



    def create_stage(
        self,
        pipeline_id: str,
        name: str,
        order: int = 1,
        probability: float = 0.0,
        is_closed: bool = False,
    ) -> PipelineStage:


        if not pipeline_id:

            raise StageManagementError(
                "Pipeline ID is required."
            )


        if not name.strip():

            raise StageManagementError(
                "Stage name is required."
            )


        if probability < 0 or probability > 1:

            raise StageManagementError(
                "Probability must be between 0 and 1."
            )


        stage = PipelineStage(

            stage_id=self._generate_id(),

            pipeline_id=pipeline_id,

            name=name,

            order=order,

            probability=probability,

            is_closed=is_closed,

        )


        self.stages.append(stage)

        return stage



    def get_stages(
        self,
        pipeline_id: str,
    ) -> list[PipelineStage]:


        stages = [

            stage

            for stage in self.stages

            if stage.pipeline_id == pipeline_id

        ]


        return sorted(
            stages,
            key=lambda x: x.order
        )



    def _generate_id(self):

        return (
            f"STAGE-{uuid.uuid4().hex[:8].upper()}"
        )