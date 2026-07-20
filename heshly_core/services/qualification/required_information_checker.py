from heshly_core.models.qualification import QualificationResult


class RequiredInformationChecker:
    """
    Checks whether all required information
    has been collected.
    """

    def check(
        self,
        collected_data: dict[str, str],
        required_fields: list[str],
        result: QualificationResult,
    ) -> QualificationResult:
        """
        Populate missing fields in the qualification result.
        """

        result.missing_fields.clear()

        for field in required_fields:

            value = collected_data.get(field)

            if value is None:
                result.missing_fields.append(field)
                continue

            if isinstance(value, str) and not value.strip():
                result.missing_fields.append(field)

        return result