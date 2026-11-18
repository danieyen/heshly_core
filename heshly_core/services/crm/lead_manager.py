from __future__ import annotations

from heshly_core.models.crm import Lead, LeadStatus

from heshly_core.repositories.repository_factory import (
    repository_factory,
)

from heshly_core.services.crm.lead_creator import (
    LeadCreator,
)

from heshly_core.services.crm.lead_assignment_manager import (
    LeadAssignmentManager,
)

from heshly_core.services.qualification.qualification_engine import (
    QualificationEngine,
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

    def __init__(self, repository=None):

        self.repository = (
            repository
            if repository is not None
            else repository_factory.leads
        )

        self.creator = LeadCreator(
            repository=self.repository
        )

        self.assignment_manager = (
            LeadAssignmentManager()
        )

        self.qualification_engine = (
            QualificationEngine()
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
        message: str = "",
        collected_data: dict[str, object] | None = None,
        required_fields: list[str] | None = None,
    ):

        collected_data = (
            collected_data
            if collected_data is not None
            else {
                "customer_name": lead.full_name,
                "phone": lead.phone,
                "email": lead.email,
                "company": lead.company,
            }
        )

        required_fields = (
            required_fields
            if required_fields is not None
            else ["customer_name", "phone"]
        )

        result, action, response = (
            self.qualification_engine.qualify(
                customer_id=lead.lead_id,
                message=message,
                collected_data=collected_data,
                required_fields=required_fields,
            )
        )

        lead.score = int(result.score)

        if result.status.value == "qualified":
            lead.status = LeadStatus.QUALIFIED
        elif result.status.value == "not_qualified":
            lead.status = LeadStatus.UNQUALIFIED

        return result, action, response


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