from heshly_core.models.whatsapp import (
    WhatsAppConfiguration,
    WhatsAppConfigurationValidation,
)


class WhatsAppConfigurationManager:
    """
    Manages and validates WhatsApp
    configuration.
    """

    def validate(
        self,
        configuration: WhatsAppConfiguration,
    ) -> WhatsAppConfigurationValidation:

        errors = []

        if not configuration.business_name.strip():
            errors.append(
                "Business name is required."
            )

        if not configuration.phone_number_id.strip():
            errors.append(
                "Phone Number ID is required."
            )

        if not configuration.business_account_id.strip():
            errors.append(
                "Business Account ID is required."
            )

        if not configuration.access_token.strip():
            errors.append(
                "Access Token is required."
            )

        if not configuration.verify_token.strip():
            errors.append(
                "Verify Token is required."
            )

        if not configuration.app_secret.strip():
            errors.append(
                "App Secret is required."
            )

        return WhatsAppConfigurationValidation(
            valid=len(errors) == 0,
            errors=errors,
        )