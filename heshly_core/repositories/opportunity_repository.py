from __future__ import annotations

from heshly_core.models.crm import (
    Opportunity,
    OpportunityStatus,
)

from heshly_core.repositories.base_repository import (
    BaseRepository,
)


class OpportunityRepository(BaseRepository[Opportunity]):
    """
    In-memory Opportunity Repository.

    This implementation satisfies the BaseRepository
    interface and can later be replaced with an
    ERPNext-backed implementation without changing
    OpportunityManager.
    """

    def __init__(self):

        self._storage: dict[str, Opportunity] = {}

    # =====================================================
    # CRUD
    # =====================================================

    def save(
        self,
        entity: Opportunity,
    ) -> Opportunity:

        self._storage[
            entity.opportunity_id
        ] = entity

        return entity

    def get(
        self,
        entity_id: str,
    ) -> Opportunity | None:

        return self._storage.get(entity_id)

    def list(self) -> list[Opportunity]:

        return list(
            self._storage.values()
        )

    def delete(
        self,
        entity_id: str,
    ) -> bool:

        if entity_id not in self._storage:
            return False

        del self._storage[entity_id]

        return True

    # =====================================================
    # Utilities
    # =====================================================

    def exists(
        self,
        entity_id: str,
    ) -> bool:

        return entity_id in self._storage

    def count(self) -> int:

        return len(self._storage)

    def clear(self) -> None:

        self._storage.clear()

    # =====================================================
    # Opportunity Queries
    # =====================================================

    def find_by_lead(
        self,
        lead_id: str,
    ) -> list[Opportunity]:

        return [

            opportunity

            for opportunity in self._storage.values()

            if opportunity.lead_id == lead_id

        ]

    def find_by_status(
        self,
        status: OpportunityStatus,
    ) -> list[Opportunity]:

        return [

            opportunity

            for opportunity in self._storage.values()

            if opportunity.status == status

        ]

    def find_by_pipeline(
        self,
        pipeline_id: str,
    ) -> list[Opportunity]:

        return [

            opportunity

            for opportunity in self._storage.values()

            if opportunity.pipeline_id == pipeline_id

        ]

    def find_by_stage(
        self,
        stage_id: str,
    ) -> list[Opportunity]:

        return [

            opportunity

            for opportunity in self._storage.values()

            if opportunity.stage_id == stage_id

        ]

    def search(
        self,
        query: str,
    ) -> list[Opportunity]:

        query = query.lower()

        results: list[
            Opportunity
        ] = []

        for opportunity in self._storage.values():

            if (
                query
                in opportunity.title.lower()
            ):

                results.append(
                    opportunity
                )

                continue

            if (
                opportunity.pipeline_id
                and query
                in opportunity.pipeline_id.lower()
            ):

                results.append(
                    opportunity
                )

                continue

            if (
                opportunity.stage_id
                and query
                in opportunity.stage_id.lower()
            ):

                results.append(
                    opportunity
                )

        return results

    def total_expected_value(
        self,
    ) -> float:

        return sum(

            opportunity.expected_value

            for opportunity
            in self._storage.values()

        )

    def total_weighted_value(
        self,
    ) -> float:

        total = 0.0

        for opportunity in self._storage.values():

            total += (

                opportunity.expected_value

                * (
                    opportunity.probability
                    / 100
                )

            )

        return total