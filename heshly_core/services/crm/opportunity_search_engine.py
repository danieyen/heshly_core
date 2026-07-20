from __future__ import annotations

from heshly_core.models.crm import (
    Opportunity,
    OpportunityStatus,
)


class OpportunitySearchEngine:
    """
    Searches and filters opportunities.
    """


    def search(
        self,
        opportunities: list[Opportunity],
        query: str | None = None,
        pipeline_id: str | None = None,
        stage_id: str | None = None,
        status: OpportunityStatus | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        min_probability: float | None = None,
    ) -> list[Opportunity]:


        results = opportunities


        # -----------------------------
        # Text Search
        # -----------------------------

        if query:

            query = query.lower()

            results = [
                opportunity
                for opportunity in results
                if query in opportunity.title.lower()
            ]


        # -----------------------------
        # Pipeline Filter
        # -----------------------------

        if pipeline_id:

            results = [
                opportunity
                for opportunity in results
                if opportunity.pipeline_id
                == pipeline_id
            ]


        # -----------------------------
        # Stage Filter
        # -----------------------------

        if stage_id:

            results = [
                opportunity
                for opportunity in results
                if opportunity.stage_id
                == stage_id
            ]


        # -----------------------------
        # Status Filter
        # -----------------------------

        if status:

            results = [
                opportunity
                for opportunity in results
                if opportunity.status
                == status
            ]


        # -----------------------------
        # Value Range
        # -----------------------------

        if min_value is not None:

            results = [
                opportunity
                for opportunity in results
                if opportunity.expected_value
                >= min_value
            ]


        if max_value is not None:

            results = [
                opportunity
                for opportunity in results
                if opportunity.expected_value
                <= max_value
            ]


        # -----------------------------
        # Probability Filter
        # -----------------------------

        if min_probability is not None:

            results = [
                opportunity
                for opportunity in results
                if opportunity.probability
                >= min_probability
            ]


        return results