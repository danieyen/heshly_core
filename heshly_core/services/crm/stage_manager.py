from __future__ import annotations

import uuid

from heshly_core.models.crm import PipelineStage

from heshly_core.repositories.repository_factory import (
    repository_factory,
)


class StageManagementError(Exception):
    pass


class StageManager:
    """
    Manages pipeline stages.

    Stages are persisted through PipelineRepository.
    """

    def __init__(self, repository=None):

        self.repository = (
            repository
            if repository is not None
            else repository_factory.pipelines
        )

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

        if not name or not name.strip():
            raise StageManagementError(
                "Stage name is required."
            )

        if probability < 0 or probability > 1:
            raise StageManagementError(
                "Probability must be between 0 and 1."
            )

        if self.repository.get(pipeline_id) is None:
            raise StageManagementError(
                f"Pipeline not found: {pipeline_id}"
            )

        stage = PipelineStage(
            stage_id=self._generate_id(),
            pipeline_id=pipeline_id,
            name=name.strip(),
            order=order,
            probability=probability,
            is_closed=is_closed,
        )

        self.repository.save_stage(stage)

        return stage

    def get_stage(
        self,
        stage_id: str,
    ) -> PipelineStage | None:

        return self.repository.get_stage(stage_id)

    def get_stages(
        self,
        pipeline_id: str,
    ) -> list[PipelineStage]:

        return self.repository.list_stages(
            pipeline_id
        )

    def delete_stage(
        self,
        stage_id: str,
    ) -> bool:

        return self.repository.delete_stage(
            stage_id
        )

    def _generate_id(self) -> str:

        return (
            f"STAGE-{uuid.uuid4().hex[:8].upper()}"
        )
