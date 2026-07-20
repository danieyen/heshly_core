from __future__ import annotations

from heshly_core.models.sms_configuration import (
    SMSConfiguration,
)

from heshly_core.repositories.sms_configuration_repository import (
    SMSConfigurationRepository,
)


class SMSConfigurationManager:
    """
    SMS Configuration Manager.
    """

    def __init__(self):

        self.repository = (
            SMSConfigurationRepository()
        )

    def save(
        self,
        configuration: SMSConfiguration,
    ) -> SMSConfiguration:

        return self.repository.save(
            configuration
        )

    def get(
        self,
        tenant_id: str,
    ) -> SMSConfiguration | None:

        return self.repository.get(
            tenant_id
        )

    def update(
        self,
        tenant_id: str,
        **kwargs,
    ) -> SMSConfiguration:

        configuration = self.get(
            tenant_id
        )

        if configuration is None:

            raise ValueError(
                "SMS configuration not found."
            )

        configuration.update(
            **kwargs
        )

        self.repository.save(
            configuration
        )

        return configuration

    def health(self):

        return {

            "service": "sms_configuration_manager",

            "status": "healthy",

        }