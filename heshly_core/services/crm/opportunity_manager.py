from __future__ import annotations

from heshly_core.models.crm import Opportunity
from heshly_core.models.opportunity import OpportunityActivityType

from heshly_core.repositories.opportunity_repository import (
    OpportunityRepository,
)

from heshly_core.services.crm.opportunity_creator import (
    OpportunityCreator,
)

from heshly_core.services.crm.opportunity_probability_manager import (
    OpportunityProbabilityManager,
)

from heshly_core.services.crm.opportunity_history_manager import (
    OpportunityHistoryManager,
)

from heshly_core.services.crm.opportunity_search_engine import (
    OpportunitySearchEngine,
)

from heshly_core.services.crm.opportunity_analytics import (
    OpportunityAnalytics,
)


class OpportunityManager:
    """
    Central Opportunity Manager.

    Single entry point for:

        - Opportunity creation
        - Probability calculation
        - History tracking
        - Searching
        - Analytics

    Future integrations:

        - Repository layer
        - ERPNext Opportunity DocType
        - Sales pipeline automation
    """

    def __init__(
        self,
        repository: OpportunityRepository | None = None,
    ):

        self.repository = (
            repository
            or OpportunityRepository()
        )

        self.creator = OpportunityCreator()

        self.probability_manager = (
            OpportunityProbabilityManager()
        )

        self.history_manager = (
            OpportunityHistoryManager()
        )

        self.search_engine = (
            OpportunitySearchEngine()
        )

        self.analytics_engine = (
            OpportunityAnalytics()
        )

    # =====================================================
    # Creation
    # =====================================================

    def create(
        self,
        **kwargs,
    ) -> Opportunity:

        opportunity = self.creator.create(
            **kwargs
        )

        self.repository.save(
            opportunity
        )

        self.history_manager.add_activity(
            opportunity_id=(
                opportunity.opportunity_id
            ),
            activity_type=(
                OpportunityActivityType.CREATED
            ),
            description="Opportunity Created",
        )

        return opportunity

    # =====================================================
    # Probability
    # =====================================================

    def calculate_probability(
        self,
        opportunity: Opportunity,
    ) -> float:

        probability = (
            self.probability_manager.calculate(
                opportunity
            )
        )

        opportunity.probability = probability

        self.repository.save(
            opportunity
        )

        self.history_manager.add_activity(
            opportunity_id=(
                opportunity.opportunity_id
            ),
            activity_type=(
                OpportunityActivityType.VALUE_UPDATED
            ),
            description=(
                "Probability updated: "
                f"{probability}%"
            ),
        )

        return probability

    # =====================================================
    # Search
    # =====================================================

    def search(
        self,
        opportunities: list[Opportunity],
        query: str,
    ) -> list[Opportunity]:

        return self.search_engine.search(
            opportunities,
            query,
        )

    # =====================================================
    # Analytics
    # =====================================================

    def analytics(
        self,
        opportunities: list[Opportunity],
    ) -> dict:

        return self.analytics_engine.summary(
            opportunities
        )

    # =====================================================
    # History
    # =====================================================

    def get_history(
        self,
        opportunity: Opportunity,
    ):

        return self.history_manager.get_history(
            opportunity.opportunity_id
        )
