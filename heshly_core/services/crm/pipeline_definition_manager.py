from __future__ import annotations

import uuid
from datetime import datetime

from heshly_core.models.crm import Pipeline


class PipelineDefinitionError(Exception):
    pass



class PipelineDefinitionManager:
    """
    Creates and manages pipeline definitions.
    """


    def create_pipeline(
        self,
        name: str,
        description: str | None = None,
        is_default: bool = False,
    ) -> Pipeline:


        if not name.strip():

            raise PipelineDefinitionError(
                "Pipeline name is required."
            )


        pipeline = Pipeline(

            pipeline_id=self._generate_id(),

            name=name,

            description=description,

            is_default=is_default,

            created_at=datetime.utcnow(),

        )


        return pipeline



    def _generate_id(self):

        return (
            f"PIPE-{uuid.uuid4().hex[:8].upper()}"
        )