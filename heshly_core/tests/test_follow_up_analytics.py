from datetime import datetime, timedelta

from heshly_core.models.follow_up import (
    FollowUp,
    FollowUpType,
    FollowUpStatus,
)

from heshly_core.services.crm.follow_up_analytics import (
    FollowUpAnalytics,
)


def run():

    analytics = FollowUpAnalytics()

    follow_ups = [

        FollowUp(

            follow_up_id="FU-001",

            business_id="BIZ-001",

            related_type="lead",

            related_id="LEAD-001",

            follow_up_type=FollowUpType.CALL,

            scheduled_for=datetime.utcnow() + timedelta(days=1),

            subject="Call",

            assigned_to="Alice",

            status=FollowUpStatus.PENDING,

        ),

        FollowUp(

            follow_up_id="FU-002",

            business_id="BIZ-001",

            related_type="lead",

            related_id="LEAD-002",

            follow_up_type=FollowUpType.EMAIL,

            scheduled_for=datetime.utcnow() + timedelta(days=2),

            subject="Email",

            assigned_to="Bob",

            status=FollowUpStatus.COMPLETED,

        ),

        FollowUp(

            follow_up_id="FU-003",

            business_id="BIZ-001",

            related_type="opportunity",

            related_id="OPP-001",

            follow_up_type=FollowUpType.WHATSAPP,

            scheduled_for=datetime.utcnow() + timedelta(days=3),

            subject="WhatsApp",

            assigned_to="Alice",

            status=FollowUpStatus.COMPLETED,

        ),

    ]

    summary = analytics.summary(
        follow_ups
    )

    print(summary)

    assert summary["total"] == 3

    assert summary["completed"] == 2

    assert summary["pending"] == 1

    assert summary["completion_rate"] == 66.67

    print(
        "\n✅ Follow-up Analytics Functional Test Passed"
    )


if __name__ == "__main__":

    run()