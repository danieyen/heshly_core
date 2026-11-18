from __future__ import annotations

from datetime import datetime, UTC

from heshly_core.models.crm import (
    Lead,
    LeadStatus,
    Opportunity,
    Pipeline,
    PipelineStage,
    CRMActivity,
    ActivityType,
)

from heshly_core.models.follow_up import (
    FollowUp,
    FollowUpType,
    FollowUpStatus,
)

from heshly_core.repositories.repository_factory import (
    repository_factory,
)


def run():

    print("=" * 60)
    print(" HESHLY CRM REPOSITORY LAYER TEST")
    print("=" * 60)

    repository_factory.clear()

    # =====================================================
    # Lead Repository
    # =====================================================

    lead = Lead(

        lead_id="LEAD-001",

        business_id="heshly",

        full_name="John Doe",

        phone="+254700000001",

        email="john@example.com",

        company="ABC Ltd",

        source="whatsapp",

        status=LeadStatus.NEW,

        score=85,

    )

    repository_factory.leads.save(lead)

    assert repository_factory.leads.count() == 1
    assert repository_factory.leads.exists("LEAD-001")
    stored_lead = repository_factory.leads.get("LEAD-001")

    assert stored_lead is not None
    assert stored_lead.lead_id == lead.lead_id
    assert stored_lead.business_id == lead.business_id
    assert stored_lead.full_name == lead.full_name
    assert stored_lead.phone == lead.phone
    assert stored_lead.email == lead.email
    assert stored_lead.company == lead.company
    assert stored_lead.source == lead.source
    assert stored_lead.status == lead.status
    assert stored_lead.score == lead.score
    assert stored_lead.assigned_to == lead.assigned_to
    assert stored_lead.created_at is not None
    assert stored_lead.updated_at is not None

    print("✓ Lead Repository")

    # =====================================================
    # Opportunity Repository
    # =====================================================

    opportunity = Opportunity(

        opportunity_id="OPP-001",

        lead_id="LEAD-001",
            tenant_id="heshly",

        title="Dental Cleaning",

        expected_value=12000,

        probability=70,

    )

    repository_factory.opportunities.save(opportunity)

    assert repository_factory.opportunities.count() == 1

    print("✓ Opportunity Repository")

    # =====================================================
    # Pipeline Repository
    # =====================================================

    pipeline = Pipeline(

        pipeline_id="PIPE-001",

        name="Default Pipeline",

        is_default=True,

    )

    repository_factory.pipelines.save(pipeline)

    stage = PipelineStage(

        stage_id="STAGE-001",

        pipeline_id="PIPE-001",

        name="Qualified",

        order=1,

        probability=0.30,

    )

    repository_factory.pipelines.save_stage(stage)

    assert repository_factory.pipelines.count() == 1
    assert repository_factory.pipelines.stage_count("PIPE-001") == 1

    print("✓ Pipeline Repository")

    # =====================================================
    # Activity Repository
    # =====================================================

    activity = CRMActivity(

        activity_id="ACT-001",

        related_type="lead",

        related_id="LEAD-001",

        activity_type=ActivityType.CALL,

        description="Called customer.",

        performed_by="Sales Agent",

    )

    repository_factory.activities.save(activity)

    assert repository_factory.activities.count() == 1

    print("✓ Activity Repository")

    # =====================================================
    # Follow-up Repository
    # =====================================================

    follow_up = FollowUp(

        follow_up_id="FU-001",

        business_id="heshly",

        related_type="lead",

        related_id="LEAD-001",

        follow_up_type=FollowUpType.CALL,

        scheduled_for=datetime.now(UTC),

        subject="Call tomorrow",

        description="Customer requested callback.",

        assigned_to="Sales Agent",

        status=FollowUpStatus.PENDING,

    )

    repository_factory.follow_ups.save(follow_up)

    assert repository_factory.follow_ups.count() == 1

    print("✓ Follow-up Repository")

    # =====================================================
    # Summary
    # =====================================================

    summary = repository_factory.summary()

    print("\nRepository Summary")

    for key, value in summary.items():

        print(f"{key}: {value}")

    assert summary["leads"] == 1
    assert summary["opportunities"] == 1
    assert summary["activities"] == 1
    assert summary["follow_ups"] == 1
    assert summary["pipelines"] == 1

    print("\n" + "=" * 60)
    print("✅ CRM REPOSITORY LAYER TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    run()
