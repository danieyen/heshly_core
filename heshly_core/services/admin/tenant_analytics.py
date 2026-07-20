from __future__ import annotations

from collections import Counter

from heshly_core.models.tenant import (
    TenantStatus,
)

from heshly_core.repositories.tenant_admin_repository import (
    TenantAdministrationRepository,
)


class TenantAnalytics:
    """
    Platform Tenant Analytics Service.
    """

    def __init__(self):

        self.repository = (
            TenantAdministrationRepository()
        )


    # =====================================================
    # Tenant Count
    # =====================================================

    def total_tenants(self) -> int:

        return self.repository.count()


    # =====================================================
    # Status Breakdown
    # =====================================================

    def status_breakdown(self):

        tenants = self.repository.list()

        return dict(
            Counter(
                tenant.status.value
                for tenant in tenants
            )
        )


    # =====================================================
    # Active Tenants
    # =====================================================

    def active_tenants(self) -> int:

        tenants = self.repository.list()

        return len(
            [
                tenant

                for tenant in tenants

                if tenant.status
                ==
                TenantStatus.ACTIVE
            ]
        )


    # =====================================================
    # Industry Breakdown
    # =====================================================

    def industry_breakdown(self):

        tenants = self.repository.list()

        industries = []

        for tenant in tenants:

            industry = (
                tenant.configuration.industry
            )

            if industry:

                industries.append(
                    industry
                )

        return dict(
            Counter(
                industries
            )
        )


    # =====================================================
    # Dashboard Summary
    # =====================================================

    def summary(self):

        return {

            "total_tenants":
                self.total_tenants(),

            "active_tenants":
                self.active_tenants(),

            "status_breakdown":
                self.status_breakdown(),

            "industry_breakdown":
                self.industry_breakdown(),

        }


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "tenant_analytics",

            "status":
                "healthy",

        }