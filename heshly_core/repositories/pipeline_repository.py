from __future__ import annotations

from heshly_core.models.crm import (
    Pipeline,
    PipelineStage,
)

from heshly_core.repositories.base_repository import (
    BaseRepository,
)


class PipelineRepository(BaseRepository[Pipeline]):
    """
    In-memory Pipeline Repository.

    Stores sales pipelines and their stages.

    This implementation satisfies the BaseRepository
    interface and can later be replaced with an
    ERPNext/Frappe repository without changing the
    PipelineManager.
    """

    def __init__(self):

        self._pipelines: dict[str, Pipeline] = {}

        self._stages: dict[str, PipelineStage] = {}

    # =====================================================
    # Pipeline CRUD
    # =====================================================

    def save(
        self,
        entity: Pipeline,
    ) -> Pipeline:

        self._pipelines[
            entity.pipeline_id
        ] = entity

        return entity

    def get(
        self,
        entity_id: str,
    ) -> Pipeline | None:

        return self._pipelines.get(entity_id)

    def list(self) -> list[Pipeline]:

        return list(
            self._pipelines.values()
        )

    def delete(
        self,
        entity_id: str,
    ) -> bool:

        if entity_id not in self._pipelines:
            return False

        # Delete all stages belonging to this pipeline
        stage_ids = [

            stage.stage_id

            for stage in self._stages.values()

            if stage.pipeline_id == entity_id

        ]

        for stage_id in stage_ids:

            del self._stages[stage_id]

        del self._pipelines[entity_id]

        return True

    # =====================================================
    # Utilities
    # =====================================================

    def exists(
        self,
        entity_id: str,
    ) -> bool:

        return entity_id in self._pipelines

    def count(self) -> int:

        return len(self._pipelines)

    def clear(self) -> None:

        self._pipelines.clear()

        self._stages.clear()

    # =====================================================
    # Pipeline Queries
    # =====================================================

    def find_by_name(
        self,
        name: str,
    ) -> Pipeline | None:

        name = name.lower()

        for pipeline in self._pipelines.values():

            if pipeline.name.lower() == name:

                return pipeline

        return None

    def default_pipeline(
        self,
    ) -> Pipeline | None:

        for pipeline in self._pipelines.values():

            if pipeline.is_default:

                return pipeline

        return None

    # =====================================================
    # Stage Management
    # =====================================================

    def save_stage(
        self,
        stage: PipelineStage,
    ) -> PipelineStage:

        self._stages[
            stage.stage_id
        ] = stage

        return stage

    def get_stage(
        self,
        stage_id: str,
    ) -> PipelineStage | None:

        return self._stages.get(stage_id)

    def delete_stage(
        self,
        stage_id: str,
    ) -> bool:

        if stage_id not in self._stages:

            return False

        del self._stages[stage_id]

        return True

    def list_stages(
        self,
        pipeline_id: str,
    ) -> list[PipelineStage]:

        stages = [

            stage

            for stage in self._stages.values()

            if (
                stage.pipeline_id
                == pipeline_id
            )

        ]

        return sorted(

            stages,

            key=lambda stage: stage.order,

        )

    def find_stage(
        self,
        stage_id: str,
    ) -> PipelineStage | None:

        return self._stages.get(stage_id)

    def next_stage(
        self,
        stage_id: str,
    ) -> PipelineStage | None:

        current = self.get_stage(stage_id)

        if current is None:

            return None

        stages = self.list_stages(
            current.pipeline_id
        )

        for index, stage in enumerate(stages):

            if (
                stage.stage_id
                == stage_id
            ):

                if index + 1 < len(stages):

                    return stages[index + 1]

                return None

        return None

    def previous_stage(
        self,
        stage_id: str,
    ) -> PipelineStage | None:

        current = self.get_stage(stage_id)

        if current is None:

            return None

        stages = self.list_stages(
            current.pipeline_id
        )

        for index, stage in enumerate(stages):

            if (
                stage.stage_id
                == stage_id
            ):

                if index > 0:

                    return stages[index - 1]

                return None

        return None

    # =====================================================
    # Search
    # =====================================================

    def search(
        self,
        query: str,
    ) -> list[Pipeline]:

        query = query.lower()

        return [

            pipeline

            for pipeline in self._pipelines.values()

            if (
                query
                in pipeline.name.lower()
            )

            or

            (
                pipeline.description
                and
                query
                in pipeline.description.lower()
            )

        ]

    # =====================================================
    # Analytics
    # =====================================================

    def stage_count(
        self,
        pipeline_id: str,
    ) -> int:

        return len(

            self.list_stages(
                pipeline_id
            )

        )

    def pipeline_summary(
        self,
    ) -> dict:

        return {

            "pipelines": self.count(),

            "stages": len(
                self._stages
            ),

            "default_pipeline": (
                self.default_pipeline().name
                if self.default_pipeline()
                else None
            ),

        }