from __future__ import annotations

from heshly_core.repositories.lead_repository import (
    LeadRepository,
)

from heshly_core.repositories.opportunity_repository import (
    OpportunityRepository,
)

from heshly_core.repositories.activity_repository import (
    ActivityRepository,
)

from heshly_core.repositories.follow_up_repository import (
    FollowUpRepository,
)

from heshly_core.repositories.pipeline_repository import (
    PipelineRepository,
)


class RepositoryFactory:
    """
    Central repository factory.

    Managers should obtain repositories through this
    factory instead of instantiating them directly.

    Today:
        - In-memory repositories

    Future:
        - ERPNext repositories
        - PostgreSQL repositories
        - REST API repositories
    """

    def __init__(self):

        # Singleton instances

        self._lead_repository = LeadRepository()

        self._opportunity_repository = (
            OpportunityRepository()
        )

        self._activity_repository = (
            ActivityRepository()
        )

        self._follow_up_repository = (
            FollowUpRepository()
        )

        self._pipeline_repository = (
            PipelineRepository()
        )

    # =====================================================
    # Lead
    # =====================================================

    @property
    def leads(self) -> LeadRepository:

        return self._lead_repository

    # =====================================================
    # Opportunity
    # =====================================================

    @property
    def opportunities(
        self,
    ) -> OpportunityRepository:

        return self._opportunity_repository

    # =====================================================
    # Activity
    # =====================================================

    @property
    def activities(
        self,
    ) -> ActivityRepository:

        return self._activity_repository

    # =====================================================
    # Follow-up
    # =====================================================

    @property
    def follow_ups(
        self,
    ) -> FollowUpRepository:

        return self._follow_up_repository

    # =====================================================
    # Pipeline
    # =====================================================

    @property
    def pipelines(
        self,
    ) -> PipelineRepository:

        return self._pipeline_repository

    # =====================================================
    # Utilities
    # =====================================================

    def clear(self) -> None:
        """
        Clears every in-memory repository.
        Useful for functional testing.
        """

        self._lead_repository.clear()

        self._opportunity_repository.clear()

        self._activity_repository.clear()

        self._follow_up_repository.clear()

        self._pipeline_repository.clear()

    def summary(self) -> dict:
        """
        Returns record counts for every repository.
        """

        return {

            "leads": self._lead_repository.count(),

            "opportunities": (
                self._opportunity_repository.count()
            ),

            "activities": (
                self._activity_repository.count()
            ),

            "follow_ups": (
                self._follow_up_repository.count()
            ),

            "pipelines": (
                self._pipeline_repository.count()
            ),

        }


# ==========================================================
# Global Factory Instance
# ==========================================================

repository_factory = RepositoryFactory()