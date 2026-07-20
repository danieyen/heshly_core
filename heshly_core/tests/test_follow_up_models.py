from datetime import datetime, timedelta

from heshly_core.models.follow_up import (
    FollowUp,
    FollowUpType,
    FollowUpStatus,
)


def run():

    follow_up = FollowUp(

        follow_up_id="FU-001",

        business_id="BIZ-001",

        related_type="opportunity",

        related_id="OPP-001",

        follow_up_type=FollowUpType.WHATSAPP,

        scheduled_for=datetime.utcnow() + timedelta(days=2),

        subject="Follow up on quotation",

        description="Check if customer has reviewed the quotation.",

        assigned_to="Sales Agent",

    )

    print(follow_up)

    assert follow_up.follow_up_id == "FU-001"

    assert follow_up.follow_up_type == (
        FollowUpType.WHATSAPP
    )

    assert follow_up.status == (
        FollowUpStatus.PENDING
    )

    print(
        "\n✅ Follow-up Models Functional Test Passed"
    )


if __name__ == "__main__":

    run()