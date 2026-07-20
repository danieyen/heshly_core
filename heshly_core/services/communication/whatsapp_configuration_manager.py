from __future__ import annotations

from heshly_core.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)

from heshly_core.repositories.whatsapp_configuration_repository import (
    WhatsAppConfigurationRepository,
)


class WhatsAppConfigurationManager:
    """
    Tenant WhatsApp Configuration Manager.
    """

    def __init__(self):

        self.repository = (
            WhatsAppConfigurationRepository()
        )

    def save(
        self,
        configuration: WhatsAppConfiguration,
    ) -> WhatsAppConfiguration:

        return self.repository.save(
            configuration
        )

    def get(
        self,
        tenant_id: str,
    ) -> WhatsAppConfiguration | None:

        return self.repository.get(
            tenant_id
        )

    def update(
        self,
        tenant_id: str,
        **kwargs,
    ) -> WhatsAppConfiguration:

        configuration = self.get(
            tenant_id
        )

        if configuration is None:

            raise ValueError(
                "WhatsApp configuration not found."
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

            "service": "whatsapp_configuration_manager",

            "status": "healthy",

        }