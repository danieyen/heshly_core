from __future__ import annotations

from heshly_core.models.email_configuration import (
    EmailConfiguration,
)

from heshly_core.repositories.email_configuration_repository import (
    EmailConfigurationRepository,
)


class EmailConfigurationManager:
    """
    Email Configuration Manager.
    """

    def __init__(self):

        self.repository = (
            EmailConfigurationRepository()
        )

    def save(
        self,
        configuration: EmailConfiguration,
    ) -> EmailConfiguration:

        return self.repository.save(
            configuration
        )

    def get(
        self,
        tenant_id: str,
    ) -> EmailConfiguration | None:

        return self.repository.get(
            tenant_id
        )

    def update(
        self,
        tenant_id: str,
        **kwargs,
    ) -> EmailConfiguration:

        configuration = self.get(
            tenant_id
        )

        if configuration is None:

            raise ValueError(
                "Email configuration not found."
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

            "service": "email_configuration_manager",

            "status": "healthy",

        }