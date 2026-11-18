from __future__ import annotations

import uuid
from datetime import datetime

from heshly_core.models.crm import Pipeline

from heshly_core.repositories.repository_factory import (
    repository_factory,
)


class PipelineDefinitionError(Exception):
    pass


class PipelineDefinitionManager:
    """
    Creates and manages pipeline definitions.

    Pipelines are persisted through the injected repository.
    """

    def __init__(self, repository=None):

        self.repository = (
            repository
            if repository is not None
            else repository_factory.pipelines
        )

    def create_pipeline(
        self,
        name: str,
        description: str | None = None,
        is_default: bool = False,
    ) -> Pipeline:

        if not name or not name.strip():
            raise PipelineDefinitionError(
                "Pipeline name is required."
            )

        pipeline = Pipeline(
            pipeline_id=self._generate_id(),
            name=name.strip(),
            description=description,
            is_default=is_default,
            created_at=datetime.utcnow(),
        )

        self.repository.save(pipeline)

        return pipeline

    def get_pipeline(
        self,
        pipeline_id: str,
    ) -> Pipeline | None:

        return self.repository.get(pipeline_id)

    def list_pipelines(self) -> list[Pipeline]:

        return self.repository.list()

    def delete_pipeline(
        self,
        pipeline_id: str,
    ) -> bool:

        return self.repository.delete(pipeline_id)

    def _generate_id(self) -> str:

        return (
            f"PIPE-{uuid.uuid4().hex[:8].upper()}"
        )
