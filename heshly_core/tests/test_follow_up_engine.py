from datetime import datetime, timedelta

from heshly_core.models.follow_up import (
    FollowUpType,
    FollowUpStatus,
)

from heshly_core.services.crm.follow_up_manager import (
    FollowUpManager,
)

from heshly_core.services.crm.escalation_rules import (
    EscalationAction,
)


def run():

    print("=" * 60)
    print(" HESHLY FOLLOW-UP ENGINE FUNCTIONAL TEST")
    print("=" * 60)

    manager = FollowUpManager()

    # ==================================================
    # 1. Manual Follow-up
    # ==================================================

    manual = manager.schedule(

        business_id="BIZ-001",

        related_type="lead",

        related_id="LEAD-001",

        follow_up_type=FollowUpType.CALL,

        scheduled_for=datetime.utcnow()
        + timedelta(days=1),

        subject="Call new lead",

        assigned_to="Sales Agent",

    )

    print("✓ Manual Follow-up Created")

    # ==================================================
    # 2. Automatic Follow-up
    # ==================================================

    automatic = manager.create_automatic(

        event="lead_created",

        business_id="BIZ-001",

        related_type="lead",

        related_id="LEAD-002",

        subject="Welcome Follow-up",

    )

    print("✓ Automatic Follow-up Created")

    # ==================================================
    # 3. Missed Appointment Recovery
    # ==================================================

    missed = manager.recover_missed_appointment(

        business_id="BIZ-001",

        appointment_id="APT-001",

        customer_name="John Doe",

    )

    print("✓ Missed Appointment Recovery")

    # ==================================================
    # 4. Lost Lead Recovery
    # ==================================================

    lost = manager.recover_lost_lead(

        business_id="BIZ-001",

        lead_id="LEAD-003",

        customer_name="Jane Doe",

        last_contact=datetime.utcnow()
        - timedelta(days=45),

    )

    print("✓ Lost Lead Recovery")

    # ==================================================
    # 5. Due Reminders
    # ==================================================

    due = manager.due_reminders(

        datetime.utcnow() + timedelta(days=10)

    )

    print(
        f"✓ Due Reminders: {len(due)}"
    )

    assert len(due) == 4

    # ==================================================
    # 6. Escalation
    # ==================================================

    overdue_follow_up = manager.schedule(

        business_id="BIZ-001",

        related_type="lead",

        related_id="LEAD-004",

        follow_up_type=FollowUpType.EMAIL,

        scheduled_for=datetime.utcnow()
        + timedelta(seconds=1),

        subject="Old Follow-up",

    )

    result = manager.evaluate_escalation(

        overdue_follow_up,

        datetime.utcnow() + timedelta(days=8),

    )

    print(
        f"✓ Escalation: {result.action.value}"
    )

    assert (
        result.action
        == EscalationAction.ESCALATE_TO_HUMAN
    )

    # ==================================================
    # 7. Complete Follow-up
    # ==================================================

    completed = manager.complete(

        manual.follow_up_id

    )

    assert (
        completed.status
        == FollowUpStatus.COMPLETED
    )

    print("✓ Follow-up Completed")

    # ==================================================
    # 8. Analytics
    # ==================================================

    summary = manager.analytics_summary()

    print("\nAnalytics Summary")

    for key, value in summary.items():

        print(f"{key}: {value}")

    assert summary["total"] == 5

    assert summary["completed"] == 1

    print("\n" + "=" * 60)
    print("✅ FOLLOW-UP ENGINE FUNCTIONAL TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":

    run()