from __future__ import annotations

from heshly_core.models.tenant import Tenant
from heshly_core.repositories.tenant_admin_repository import (
    TenantAdministrationRepository,
)
from heshly_core.services.base_manager import (
    BaseManager,
)


class TenantAdministration(
    BaseManager
):
    """
    Platform Tenant Administration.
    """

    SERVICE_NAME = "tenant_administration"

    def __init__(self):

        super().__init__()

        self.repository = (
            TenantAdministrationRepository()
        )

    def register(
        self,
        tenant: Tenant,
    ) -> Tenant:

        return self.repository.save(
            tenant
        )

    def get(
        self,
        tenant_id: str,
    ) -> Tenant | None:

        return self.repository.get(
            tenant_id
        )

    def list(self) -> list[Tenant]:

        return self.repository.list()

    def suspend(
        self,
        tenant_id: str,
    ) -> bool:

        tenant = self.get(
            tenant_id
        )

        if tenant is None:

            return False

        tenant.suspend()

        self.repository.save(
            tenant
        )

        return True


    def activate(
        self,
        tenant_id: str,
    ) -> bool:

        tenant = self.get(
            tenant_id
        )

        if tenant is None:

            return False

        tenant.activate()

        self.repository.save(
            tenant
        )

        return True
        return True

    def remove(
        self,
        tenant_id: str,
    ) -> bool:

        tenant = self.get(
            tenant_id
        )

        if tenant is None:

            return False

        tenant.delete()

        self.repository.save(
            tenant
        )

        return True