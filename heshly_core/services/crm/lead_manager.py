from __future__ import annotations

from heshly_core.models.crm import Lead, LeadStatus

from heshly_core.services.crm.lead_creator import (
    LeadCreator,
)

from heshly_core.services.crm.lead_assignment_manager import (
    LeadAssignmentManager,
)

from heshly_core.services.crm.lead_qualification_manager import (
    LeadQualificationManager,
)

from heshly_core.services.crm.lead_scoring_engine import (
    LeadScoringEngine,
)

from heshly_core.services.crm.lead_status_manager import (
    LeadStatusManager,
)

from heshly_core.services.crm.lead_search_engine import (
    LeadSearchEngine,
)


class LeadManager:
    """
    Main CRM Lead facade.
    """

    def __init__(self):

        self.creator = LeadCreator()

        self.assignment_manager = (
            LeadAssignmentManager()
        )

        self.qualification_manager = (
            LeadQualificationManager()
        )

        self.scoring_engine = (
            LeadScoringEngine()
        )

        self.status_manager = (
            LeadStatusManager()
        )

        self.search_engine = (
            LeadSearchEngine()
        )


    # -----------------------------------------
    # Creation
    # -----------------------------------------

    def create_lead(
        self,
        business_id: str,
        full_name: str,
        phone: str | None = None,
        email: str | None = None,
        company: str | None = None,
        source: str = "whatsapp",
    ) -> Lead:

        return self.creator.create(
            business_id,
            full_name,
            phone,
            email,
            company,
            source,
        )


    # -----------------------------------------
    # Assignment
    # -----------------------------------------

    def assign_lead(
        self,
        lead: Lead,
        assigned_to: str,
    ):

        return self.assignment_manager.assign(
            lead,
            assigned_to,
        )


    # -----------------------------------------
    # Qualification
    # -----------------------------------------

    def qualify_lead(
        self,
        lead: Lead,
    ):

        return self.qualification_manager.qualify(
            lead
        )


    # -----------------------------------------
    # Scoring
    # -----------------------------------------

    def score_lead(
        self,
        lead: Lead,
    ):

        return self.scoring_engine.calculate(
            lead
        )


    # -----------------------------------------
    # Status
    # -----------------------------------------

    def update_status(
        self,
        lead: Lead,
        status: LeadStatus,
    ):

        return self.status_manager.change_status(
            lead,
            status,
        )


    # -----------------------------------------
    # Search
    # -----------------------------------------

    def search_leads(
        self,
        leads: list[Lead],
        query: str | None = None,
        status: LeadStatus | None = None,
        assigned_to: str | None = None,
        min_score: int | None = None,
    ):

        return self.search_engine.search(
            leads,
            query,
            status,
            assigned_to,
            min_score,
        )