from __future__ import annotations

from heshly_core.services.admin.tenant_administration import (
    TenantAdministration,
)

from heshly_core.services.admin.tenant_analytics import (
    TenantAnalytics,
)

from heshly_core.services.admin.system_monitor import (
    SystemMonitor,
)


class AdminDashboard:
    """
    Heshly Platform Admin Dashboard.

    Aggregates platform administration
    information.
    """

    def __init__(self):

        self.tenant_admin = (
            TenantAdministration()
        )

        self.tenant_analytics = (
            TenantAnalytics()
        )

        self.system_monitor = (
            SystemMonitor()
        )


    # =====================================================
    # Dashboard Summary
    # =====================================================

    def overview(self):

        return {

            "tenants": {

                "total":
                    self.tenant_analytics.total_tenants(),

                "active":
                    self.tenant_analytics.active_tenants(),

                "status":
                    self.tenant_analytics.status_breakdown(),

            },


            "system":

                self.system_monitor.system_status(),

        }


    # =====================================================
    # Tenant Section
    # =====================================================

    def tenant_summary(self):

        return {

            "total":
                self.tenant_analytics.total_tenants(),

            "industries":
                self.tenant_analytics.industry_breakdown(),

        }


    # =====================================================
    # System Section
    # =====================================================

    def system_summary(self):

        return (

            self.system_monitor.health_report()

        )


    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "service":
                "admin_dashboard",

            "status":
                "healthy",

        }