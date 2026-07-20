from __future__ import annotations

from heshly_core.models.crm import Lead, LeadStatus


class LeadSearchEngine:
    """
    Handles lead searching and filtering.
    """

    def search(
        self,
        leads: list[Lead],
        query: str | None = None,
        status: LeadStatus | None = None,
        assigned_to: str | None = None,
        min_score: int | None = None,
    ) -> list[Lead]:

        results = leads


        # -----------------------------------
        # Text Search
        # -----------------------------------

        if query:

            query = query.lower()

            results = [
                lead
                for lead in results
                if (
                    query in lead.full_name.lower()
                    or (
                        lead.phone
                        and query in lead.phone
                    )
                    or (
                        lead.email
                        and query in lead.email.lower()
                    )
                )
            ]


        # -----------------------------------
        # Status Filter
        # -----------------------------------

        if status:

            results = [
                lead
                for lead in results
                if lead.status == status
            ]


        # -----------------------------------
        # Assignment Filter
        # -----------------------------------

        if assigned_to:

            results = [
                lead
                for lead in results
                if lead.assigned_to == assigned_to
            ]


        # -----------------------------------
        # Score Filter
        # -----------------------------------

        if min_score is not None:

            results = [
                lead
                for lead in results
                if lead.score >= min_score
            ]


        return results