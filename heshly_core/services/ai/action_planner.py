from heshly_core.models.intent import Intent
from heshly_core.models.workflow import (
    Action,
    ActionPlan,
    CompletenessResult,
    RuleResult,
)


class ActionPlanner:
    """
    Determines the next action for the AI Receptionist.

    Priority:
    1. Collect missing information.
    2. Validate business rules.
    3. Execute the requested action.
    """

    def plan(
        self,
        intent: Intent,
        completeness: CompletenessResult,
        rules: RuleResult | None = None,
    ) -> ActionPlan:

        # Step 1: Gather missing information first.
        if not completeness.complete:

            if "service" in completeness.missing_fields:
                return ActionPlan(
                    Action.ASK_SERVICE,
                    "Customer has not selected a service."
                )

            if "date" in completeness.missing_fields:
                return ActionPlan(
                    Action.ASK_DATE,
                    "Customer has not selected a date."
                )

            if "time" in completeness.missing_fields:
                return ActionPlan(
                    Action.ASK_TIME,
                    "Customer has not selected a time."
                )

        # Step 2: Only evaluate business rules once we have
        # everything we need.
        if rules is not None and not rules.allowed:
            return ActionPlan(
                Action.ESCALATE_HUMAN,
                rules.reason or "Business rule failed."
            )

        # Step 3: Execute the requested intent.
        if intent == Intent.BOOK_APPOINTMENT:
            return ActionPlan(
                Action.CREATE_APPOINTMENT,
                "Appointment can now be created."
            )

        return ActionPlan(
            Action.UNKNOWN,
            "No action available."
        )