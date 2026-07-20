from heshly_core.models.conversation import ExtractedEntities
from heshly_core.models.intent import Intent
from heshly_core.models.workflow import CompletenessResult


class CompletenessChecker:
    """
    Determines whether enough information has
    been collected to continue.
    """

    REQUIRED_FIELDS = {
        Intent.BOOK_APPOINTMENT: [
            "service",
            "date",
            "time",
        ],
    }

    def check(
        self,
        intent: Intent,
        entities: ExtractedEntities,
    ) -> CompletenessResult:

        required = self.REQUIRED_FIELDS.get(intent, [])

        missing = []

        for field_name in required:
            if getattr(entities, field_name) is None:
                missing.append(field_name)

        return CompletenessResult(
            complete=len(missing) == 0,
            missing_fields=missing,
        )