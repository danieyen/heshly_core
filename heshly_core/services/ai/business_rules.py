from heshly_core.models.intent import Intent
from heshly_core.models.conversation import ExtractedEntities
from heshly_core.models.workflow import RuleResult


class BusinessRules:
    """
    Applies business policies before any action
    is taken.
    """

    VALID_SERVICES = {
        "Dental Cleaning",
        "Consultation",
        "Checkup",
        "Whitening",
        "Filling",
    }

    def evaluate(
        self,
        intent: Intent,
        entities: ExtractedEntities,
    ) -> RuleResult:

        if intent == Intent.BOOK_APPOINTMENT:

            if entities.service not in self.VALID_SERVICES:
                return RuleResult(
                    allowed=False,
                    reason="Unknown service."
                )

        return RuleResult(
            allowed=True,
            reason=None
        )