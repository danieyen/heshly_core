from __future__ import annotations

from heshly_core.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)


class WhatsAppConfigurationRepository:

    def __init__(self):

        self._storage: dict[
            str,
            WhatsAppConfiguration,
        ] = {}

    def save(
        self,
        configuration: WhatsAppConfiguration,
    ) -> WhatsAppConfiguration:

        self._storage[
            configuration.tenant_id
        ] = configuration

        return configuration

    def get(
        self,
        tenant_id: str,
    ) -> WhatsAppConfiguration | None:

        return self._storage.get(
            tenant_id
        )

    def exists(
        self,
        tenant_id: str,
    ) -> bool:

        return tenant_id in self._storage

    def delete(
        self,
        tenant_id: str,
    ) -> bool:

        return self._storage.pop(
            tenant_id,
            None,
        ) is not None