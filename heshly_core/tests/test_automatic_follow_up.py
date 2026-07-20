from heshly_core.models.follow_up import (
    FollowUpType,
)

from heshly_core.services.crm.automatic_follow_up import (
    AutomaticFollowUp,
)

from heshly_core.services.crm.reminder_scheduler import (
    ReminderScheduler,
)


def run():

    scheduler = ReminderScheduler()

    engine = AutomaticFollowUp(
        scheduler
    )


    follow_up = engine.create_follow_up(

        event="lead_created",

        business_id="BIZ-001",

        related_type="lead",

        related_id="LEAD-001",

        subject="Call new lead",

        assigned_to="Sales Agent",

        follow_up_type=FollowUpType.CALL,

    )


    print("Automatic Follow-up:")
    print(follow_up)


    assert follow_up.related_type == "lead"

    assert follow_up.related_id == "LEAD-001"

    assert follow_up.subject == "Call new lead"

    assert len(
        scheduler.follow_ups
    ) == 1


    print(
        "\n✅ Automatic Follow-up Functional Test Passed"
    )


if __name__ == "__main__":

    run()