from heshly_core.models.activity import (
    Activity,
    ActivityStatus,
    ActivityPriority,
)



def run():


    activity = Activity(

        activity_id="ACT-001",

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        activity_type="whatsapp",

        subject="Follow up quotation",

        description="Send treatment quotation reminder",

        assigned_to="Sales Agent",

    )


    print(activity)


    assert activity.activity_id == (
        "ACT-001"
    )


    assert activity.status == (
        ActivityStatus.PENDING
    )


    assert activity.priority == (
        ActivityPriority.MEDIUM
    )


    assert activity.related_type == (
        "opportunity"
    )


    print(
        "\n✅ Activity Models Functional Test Passed"
    )



if __name__ == "__main__":
    run()