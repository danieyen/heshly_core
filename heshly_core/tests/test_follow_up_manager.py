from datetime import datetime, timedelta

from heshly_core.models.follow_up import (
    FollowUpType,
)

from heshly_core.services.crm.follow_up_manager import (
    FollowUpManager,
)


def run():

    manager = FollowUpManager()

    # -----------------------------------
    # Schedule Reminder
    # -----------------------------------

    reminder = manager.schedule(

        business_id="BIZ-001",

        related_type="lead",

        related_id="LEAD-001",

        follow_up_type=FollowUpType.CALL,

        scheduled_for=(
            datetime.utcnow()
            + timedelta(days=1)
        ),

        subject="Call customer",

    )

    print("✓ Reminder Scheduled")

    # -----------------------------------
    # Automatic Follow-up
    # -----------------------------------

    manager.create_automatic(

        event="lead_created",

        business_id="BIZ-001",

        related_type="lead",

        related_id="LEAD-002",

        subject="Welcome follow-up",

    )

    print("✓ Automatic Follow-up")

    # -----------------------------------
    # Missed Appointment
    # -----------------------------------

    manager.recover_missed_appointment(

        business_id="BIZ-001",

        appointment_id="APT-001",

        customer_name="John Doe",

    )

    print("✓ Missed Appointment Recovery")

    # -----------------------------------
    # Lost Lead
    # -----------------------------------

    manager.recover_lost_lead(

        business_id="BIZ-001",

        lead_id="LEAD-003",

        customer_name="Jane Doe",

        last_contact=(
            datetime.utcnow()
            - timedelta(days=40)
        ),

    )

    print("✓ Lost Lead Recovery")

    # -----------------------------------
    # Analytics
    # -----------------------------------

    summary = manager.analytics_summary()

    print(summary)

    assert summary["total"] == 4

    print("\n✅ FollowUpManager Functional Test Passed")


if __name__ == "__main__":
    run()