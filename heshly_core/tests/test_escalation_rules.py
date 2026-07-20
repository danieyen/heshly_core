from datetime import datetime, timedelta

from heshly_core.models.follow_up import (
    FollowUp,
    FollowUpType,
)

from heshly_core.services.crm.escalation_rules import (
    EscalationRules,
    EscalationAction,
)


def run():

    rules = EscalationRules()

    follow_up = FollowUp(

        follow_up_id="FU-001",

        business_id="BIZ-001",

        related_type="lead",

        related_id="LEAD-001",

        follow_up_type=FollowUpType.CALL,

        scheduled_for=datetime.utcnow() - timedelta(days=5),

        subject="Call customer",

        assigned_to="Sales Agent",

    )

    result = rules.evaluate(

        follow_up,

        datetime.utcnow(),

    )

    print(result)

    assert result.escalated is True

    assert (
        result.action
        == EscalationAction.NOTIFY_MANAGER
    )

    print(
        "\n✅ Escalation Rules Functional Test Passed"
    )


if __name__ == "__main__":

    run()