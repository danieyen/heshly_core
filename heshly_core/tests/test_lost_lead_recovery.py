from datetime import datetime, timedelta

from heshly_core.services.crm.lost_lead_recovery import (
    LostLeadRecovery,
)

from heshly_core.services.crm.reminder_scheduler import (
    ReminderScheduler,
)


def run():

    scheduler = ReminderScheduler()

    recovery = LostLeadRecovery(
        scheduler
    )

    follow_up = recovery.recover(

        business_id="BIZ-001",

        lead_id="LEAD-001",

        customer_name="John Doe",

        last_contact=(
            datetime.utcnow()
            - timedelta(days=45)
        ),

        assigned_to="Sales Agent",

    )

    print("Recovery Follow-up:")
    print(follow_up)

    assert follow_up.related_type == "lead"

    assert follow_up.related_id == "LEAD-001"

    assert "Recover lost lead" in (
        follow_up.subject
    )

    assert len(
        scheduler.follow_ups
    ) == 1

    print(
        "\n✅ Lost Lead Recovery Functional Test Passed"
    )


if __name__ == "__main__":

    run()