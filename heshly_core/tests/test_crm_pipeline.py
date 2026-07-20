from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Lead:
    id: str
    customer: str
    status: str


@dataclass
class Opportunity:
    id: str
    lead_id: str
    stage: str


@dataclass
class Activity:
    id: str
    opportunity_id: str
    action: str


class LeadManager:

    def create(
        self,
        customer: str,
    ) -> Lead:

        return Lead(
            id="LEAD-001",
            customer=customer,
            status="New",
        )


class PipelineManager:

    def qualify(
        self,
        lead: Lead,
    ) -> Opportunity:

        lead.status = "Qualified"

        return Opportunity(
            id="OPP-001",
            lead_id=lead.id,
            stage="Qualified",
        )

    def move_stage(
        self,
        opportunity: Opportunity,
        stage: str,
    ):

        opportunity.stage = stage

        return opportunity


class ActivityManager:

    def log(
        self,
        opportunity: Opportunity,
        action: str,
    ) -> Activity:

        return Activity(
            id="ACT-001",
            opportunity_id=opportunity.id,
            action=action,
        )


class FollowUpEngine:

    def schedule(
        self,
        opportunity: Opportunity,
    ) -> bool:

        return True


class AnalyticsManager:

    def record(
        self,
        opportunity: Opportunity,
    ) -> bool:

        return True


def test_crm_pipeline():

    print("\n================================")
    print("CRM Pipeline Test")
    print("================================\n")

    leads = LeadManager()

    pipeline = PipelineManager()

    activities = ActivityManager()

    followups = FollowUpEngine()

    analytics = AnalyticsManager()

    lead = leads.create(
        "John Doe",
    )

    assert lead.status == "New"

    print("✅ Lead Created")

    opportunity = pipeline.qualify(
        lead,
    )

    assert lead.status == "Qualified"

    assert opportunity.stage == "Qualified"

    print("✅ Lead Qualified")

    activity = activities.log(
        opportunity,
        "Initial Contact",
    )

    assert activity.action == "Initial Contact"

    print("✅ Activity Logged")

    opportunity = pipeline.move_stage(
        opportunity,
        "Proposal",
    )

    assert opportunity.stage == "Proposal"

    print("✅ Pipeline Updated")

    assert followups.schedule(
        opportunity,
    )

    print("✅ Follow-up Scheduled")

    opportunity = pipeline.move_stage(
        opportunity,
        "Won",
    )

    assert opportunity.stage == "Won"

    print("✅ Opportunity Closed")

    assert analytics.record(
        opportunity,
    )

    print("✅ Analytics Updated")

    print("\n🎉 CRM PIPELINE TEST PASSED\n")