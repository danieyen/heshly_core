from datetime import datetime, timedelta

from heshly_core.models.follow_up import (
    FollowUpType,
    FollowUpStatus,
)

from heshly_core.services.crm.reminder_scheduler import (
    ReminderScheduler,
)


def run():

    scheduler = ReminderScheduler()


    follow_up = scheduler.schedule(

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        follow_up_type=FollowUpType.CALL,

        scheduled_for=datetime.utcnow() + timedelta(seconds=1),

        subject="Call customer",

        description="Discuss quotation",

        assigned_to="Sales Agent",

    )


    print("Scheduled:")
    print(follow_up)


    assert follow_up.status == (
        FollowUpStatus.PENDING
    )


    # Simulate time passing
    due = scheduler.due_reminders(
        datetime.utcnow() + timedelta(seconds=2)
    )

    print("\nDue Reminders:")
    print(due)

    assert len(due) == 1


    completed = scheduler.complete(
        follow_up.follow_up_id
    )

    print("\nCompleted:")
    print(completed)

    assert completed.status == (
        FollowUpStatus.COMPLETED
    )


    print(
        "\n✅ Reminder Scheduler Functional Test Passed"
    )


if __name__ == "__main__":

    run()