from datetime import date, datetime

from heshly_core.models.crm import (
    Lead,
    LeadStatus,
    Opportunity,
    Pipeline,
    PipelineStage,
    CRMActivity,
    CRMTask,
    CRMNote,
    Quote,
    QuoteItem,
    FollowUp,
    CustomerJourneyEvent,
    CRMAnalyticsSnapshot,
    ActivityType,
)


def run():

    # --------------------------------------------------
    # Lead
    # --------------------------------------------------
    lead = Lead(
        lead_id="LEAD-0001",
        business_id="BIZ-001",
        full_name="John Doe",
        phone="+254700123456",
        email="john@example.com",
    )

    print("Lead")
    print(lead)
    assert lead.status == LeadStatus.NEW

    # --------------------------------------------------
    # Opportunity
    # --------------------------------------------------
    opportunity = Opportunity(
        opportunity_id="OPP-0001",
        lead_id=lead.lead_id,
        title="Dental Implant",
        expected_value=45000,
        probability=0.75,
    )

    print("\nOpportunity")
    print(opportunity)

    # --------------------------------------------------
    # Pipeline
    # --------------------------------------------------
    pipeline = Pipeline(
        pipeline_id="PIPE-001",
        name="Sales Pipeline",
        is_default=True,
    )

    stage = PipelineStage(
        stage_id="STAGE-001",
        pipeline_id=pipeline.pipeline_id,
        name="Qualified",
        order=2,
        probability=40,
    )

    print("\nPipeline")
    print(pipeline)

    print("\nStage")
    print(stage)

    # --------------------------------------------------
    # Activity
    # --------------------------------------------------
    activity = CRMActivity(
        activity_id="ACT-001",
        related_type="Lead",
        related_id=lead.lead_id,
        activity_type=ActivityType.WHATSAPP,
        description="Customer sent first WhatsApp message.",
    )

    print("\nActivity")
    print(activity)

    # --------------------------------------------------
    # Task
    # --------------------------------------------------
    task = CRMTask(
        task_id="TASK-001",
        related_type="Lead",
        related_id=lead.lead_id,
        title="Call customer",
    )

    print("\nTask")
    print(task)

    # --------------------------------------------------
    # Note
    # --------------------------------------------------
    note = CRMNote(
        note_id="NOTE-001",
        related_type="Lead",
        related_id=lead.lead_id,
        content="Interested in premium package.",
    )

    print("\nNote")
    print(note)

    # --------------------------------------------------
    # Quote
    # --------------------------------------------------
    quote = Quote(
        quote_id="Q-001",
        opportunity_id=opportunity.opportunity_id,
        valid_until=date.today(),
    )

    quote.items.append(
        QuoteItem(
            item_name="Dental Implant",
            quantity=1,
            unit_price=45000,
        )
    )

    quote.items.append(
        QuoteItem(
            item_name="Consultation",
            quantity=1,
            unit_price=5000,
        )
    )

    print("\nQuote")
    print(quote)
    print("Subtotal:", quote.subtotal)
    print("Total:", quote.total)

    assert quote.total == 50000

    # --------------------------------------------------
    # Follow-up
    # --------------------------------------------------
    follow_up = FollowUp(
        follow_up_id="FU-001",
        related_type="Lead",
        related_id=lead.lead_id,
        scheduled_for=datetime.now(),
    )

    print("\nFollow Up")
    print(follow_up)

    # --------------------------------------------------
    # Journey
    # --------------------------------------------------
    journey = CustomerJourneyEvent(
        event_id="J-001",
        customer_id=lead.lead_id,
        stage="Qualified",
        source="WhatsApp",
    )

    print("\nJourney")
    print(journey)

    # --------------------------------------------------
    # Analytics
    # --------------------------------------------------
    analytics = CRMAnalyticsSnapshot(
        business_id="BIZ-001",
        snapshot_date=date.today(),
        total_leads=12,
        qualified_leads=8,
        open_opportunities=4,
        won_opportunities=2,
        pipeline_value=125000,
        conversion_rate=66.7,
    )

    print("\nAnalytics")
    print(analytics)

    print("\n✅ CRM Models Functional Test Passed")


if __name__ == "__main__":
    run()