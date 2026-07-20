from __future__ import annotations

from heshly_core.models.email_configuration import (
    EmailConfiguration,
)


class EmailConfigurationRepository:

    def __init__(self):

        self._storage: dict[
            str,
            EmailConfiguration,
        ] = {}

    def save(
        self,
        configuration: EmailConfiguration,
    ) -> EmailConfiguration:

        self._storage[
            configuration.tenant_id
        ] = configuration

        return configuration

    def get(
        self,
        tenant_id: str,
    ) -> EmailConfiguration | None:

        return self._storage.get(
            tenant_id
        )

    def delete(
        self,
        tenant_id: str,
    ) -> bool:

        return self._storage.pop(
            tenant_id,
            None,
        ) is not None

    def exists(
        self,
        tenant_id: str,
    ) -> bool:

        return tenant_id in self._storage