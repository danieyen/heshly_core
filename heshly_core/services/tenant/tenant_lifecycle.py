from __future__ import annotations


from heshly_core.models.tenant import (
    Tenant,
    TenantStatus,
)

from heshly_core.services.tenant.tenant_manager import (
    TenantManager,
)



class TenantLifecycle:
    """
    Tenant Lifecycle Manager.

    Controls tenant state transitions.

    Supported lifecycle:

        TRIAL
          |
          ↓
        ACTIVE
          |
          ↓
      SUSPENDED
          |
          ↓
       DELETED


    Responsibilities:

    - Tenant creation
    - Tenant activation
    - Tenant suspension
    - Tenant deletion
    - Lifecycle validation
    """

    def __init__(self):

        self.manager = TenantManager()


    # =====================================================
    # Create Tenant
    # =====================================================

    def create_tenant(
        self,
        tenant: Tenant,
    ) -> Tenant:

        if tenant.status != TenantStatus.TRIAL:

            raise ValueError(
                "New tenants must start as TRIAL"
            )


        return self.manager.create(
            tenant
        )


    # =====================================================
    # Activate Tenant
    # =====================================================

    def activate_tenant(
        self,
        tenant_id: str,
    ) -> Tenant:


        tenant = self.manager.get(
            tenant_id
        )


        self._validate_exists(
            tenant
        )


        if tenant.status == TenantStatus.DELETED:

            raise ValueError(
                "Deleted tenant cannot be activated"
            )


        return self.manager.activate(
            tenant_id
        )


    # =====================================================
    # Suspend Tenant
    # =====================================================

    def suspend_tenant(
        self,
        tenant_id: str,
    ) -> Tenant:


        tenant = self.manager.get(
            tenant_id
        )


        self._validate_exists(
            tenant
        )


        if tenant.status == TenantStatus.DELETED:

            raise ValueError(
                "Deleted tenant cannot be suspended"
            )


        return self.manager.suspend(
            tenant_id
        )


    # =====================================================
    # Delete Tenant
    # =====================================================

    def delete_tenant(
        self,
        tenant_id: str,
    ) -> Tenant:


        tenant = self.manager.get(
            tenant_id
        )


        self._validate_exists(
            tenant
        )


        return self.manager.delete(
            tenant_id
        )


    # =====================================================
    # Lifecycle State
    # =====================================================

    def status(
        self,
        tenant_id: str,
    ) -> TenantStatus:


        tenant = self.manager.get(
            tenant_id
        )


        self._validate_exists(
            tenant
        )


        return tenant.status



    # =====================================================
    # Validation
    # =====================================================

    def can_activate(
        self,
        tenant: Tenant,
    ) -> bool:


        return tenant.status in [

            TenantStatus.TRIAL,

            TenantStatus.SUSPENDED,

        ]


    def can_suspend(
        self,
        tenant: Tenant,
    ) -> bool:


        return tenant.status == TenantStatus.ACTIVE



    def can_delete(
        self,
        tenant: Tenant,
    ) -> bool:


        return tenant.status != TenantStatus.DELETED



    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "tenant_lifecycle",

            "status": "healthy",

        }


    # =====================================================
    # Internal
    # =====================================================

    def _validate_exists(
        self,
        tenant: Tenant | None,
    ):


        if tenant is None:

            raise ValueError(
                "Tenant does not exist"
            )