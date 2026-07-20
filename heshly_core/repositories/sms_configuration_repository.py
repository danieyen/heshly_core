from __future__ import annotations

from heshly_core.models.sms_configuration import (
    SMSConfiguration,
)


class SMSConfigurationRepository:

    def __init__(self):

        self._storage: dict[
            str,
            SMSConfiguration,
        ] = {}

    def save(
        self,
        configuration: SMSConfiguration,
    ) -> SMSConfiguration:

        self._storage[
            configuration.tenant_id
        ] = configuration

        return configuration

    def get(
        self,
        tenant_id: str,
    ) -> SMSConfiguration | None:

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