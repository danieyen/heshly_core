from heshly_core.models.qualification import (
    QualificationResult,
)


class EligibilityEvaluator:
    """
    Evaluates whether a customer is eligible
    to proceed with the requested service.
    """

    def evaluate(
        self,
        collected_data: dict[str, object],
        result: QualificationResult,
    ) -> QualificationResult:

        # Reset evaluation
        result.eligible = True
        result.eligibility_reason = None

        # Guardian rule
        age = collected_data.get("age")
        guardian = collected_data.get("guardian_present")

        if (
            isinstance(age, int)
            and age < 18
            and not guardian
        ):
            result.eligible = False
            result.eligibility_reason = (
                "Guardian is required for customers under 18."
            )
            return result

        # Policy number rule
        requires_policy = collected_data.get(
            "requires_policy"
        )

        if (
            requires_policy
            and not collected_data.get("policy_number")
        ):
            result.eligible = False
            result.eligibility_reason = (
                "A valid policy number is required."
            )
            return result

        # Service availability rule
        available = collected_data.get(
            "service_available",
            True,
        )

        if not available:
            result.eligible = False
            result.eligibility_reason = (
                "Requested service is currently unavailable."
            )
            return result

        return result