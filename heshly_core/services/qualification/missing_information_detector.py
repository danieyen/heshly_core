from heshly_core.models.qualification import QualificationResult


class MissingInformationDetector:
    """
    Determines the next piece of information
    the AI should request from the customer.
    """

    DEFAULT_QUESTIONS = {
        "service":
            "What service would you like to book?",

        "preferred_date":
            "What day would you prefer?",

        "preferred_time":
            "What time works best for you?",

        "customer_name":
            "May I have your name?",

        "phone":
            "What phone number should we use?",

        "email":
            "What email address should we use?",
    }

    def next_question(
        self,
        result: QualificationResult,
    ) -> str | None:
        """
        Return the next question to ask.
        """

        if not result.missing_fields:
            return None

        next_field = result.missing_fields[0]

        return self.DEFAULT_QUESTIONS.get(
            next_field,
            f"Please provide your {next_field.replace('_', ' ')}."
        )