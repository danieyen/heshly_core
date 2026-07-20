from __future__ import annotations


from heshly_core.models.tenant import (
    Tenant,
)

from heshly_core.repositories.tenant_repository import (
    TenantRepository,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContextManager,
)



class TenantResolver:
    """
    Tenant Resolver.

    Identifies the tenant associated
    with an incoming request.

    Resolution methods:

    - Tenant ID
    - Email
    - Phone
    - External identifier

    Future:

    - WhatsApp Business Number
    - API Key
    - Domain
    - ERPNext Company
    """



    def __init__(self):

        self.repository = TenantRepository()

        self.context = TenantContextManager()



    # =====================================================
    # Resolve By Tenant ID
    # =====================================================

    def resolve_by_id(
        self,
        tenant_id: str,
    ) -> Tenant | None:


        tenant = self.repository.get(
            tenant_id
        )


        if tenant:

            self.context.set(
                tenant
            )


        return tenant



    # =====================================================
    # Resolve By Email
    # =====================================================

    def resolve_by_email(
        self,
        email: str,
    ) -> Tenant | None:


        tenants = self.repository.all()


        for tenant in tenants:


            if tenant.email == email:

                self.context.set(
                    tenant
                )

                return tenant



        return None



    # =====================================================
    # Resolve By Phone
    # =====================================================

    def resolve_by_phone(
        self,
        phone: str,
    ) -> Tenant | None:


        tenants = self.repository.all()


        for tenant in tenants:


            if tenant.phone == phone:

                self.context.set(
                    tenant
                )

                return tenant



        return None



    # =====================================================
    # Current Tenant
    # =====================================================

    def current(self) -> Tenant | None:

        return self.context.get()



    # =====================================================
    # Clear
    # =====================================================

    def clear(self):

        self.context.clear()



    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service": "tenant_resolver",

            "status": "healthy",

        }