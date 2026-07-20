from heshly_core.models.personality import (
    PersonalityProfile,
    PersonalityValidationError,
    PersonalityValidationResult,
)


class PersonalityValidator:
    """
    Validates receptionist personality profiles.
    """

    def validate(
        self,
        profile: PersonalityProfile,
    ) -> PersonalityValidationResult:

        errors = []

        if not profile.name.strip():

            errors.append(
                PersonalityValidationError(
                    field="name",
                    message="Personality name is required.",
                )
            )

        if not profile.brand_voice.business_name.strip():

            errors.append(
                PersonalityValidationError(
                    field="business_name",
                    message="Business name is required.",
                )
            )

        if not profile.brand_voice.industry.strip():

            errors.append(
                PersonalityValidationError(
                    field="industry",
                    message="Industry is required.",
                )
            )

        if not profile.language.language_code.strip():

            errors.append(
                PersonalityValidationError(
                    field="language_code",
                    message="Language code is required.",
                )
            )

        if not profile.language.language_name.strip():

            errors.append(
                PersonalityValidationError(
                    field="language_name",
                    message="Language name is required.",
                )
            )

        if not profile.language.locale.strip():

            errors.append(
                PersonalityValidationError(
                    field="locale",
                    message="Locale is required.",
                )
            )

        return PersonalityValidationResult(
            valid=len(errors) == 0,
            errors=errors,
        )