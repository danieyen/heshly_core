from __future__ import annotations

from heshly_core.services.analytics.analytics_manager import AnalyticsManager
from heshly_core.services.dashboard.dashboard_manager import DashboardManager
from heshly_core.services.appointment_analytics.appointment_manager import (
    AppointmentAnalyticsManager,
)
from heshly_core.services.customer_analytics.customer_analytics_manager import (
    CustomerAnalyticsManager,
)
from heshly_core.services.sales_analytics.sales_manager import (
    SalesAnalyticsManager,
)
from heshly_core.services.ai_analytics.ai_analytics_manager import (
    AIAnalyticsManager,
)
from heshly_core.services.marketing_analytics.marketing_manager import (
    MarketingAnalyticsManager,
)
from heshly_core.services.reporting.report_manager import (
    ReportManager,
)
from heshly_core.services.business_intelligence.bi_manager import (
    BIManager,
)


class AnalyticsIntegration:
    """
    Analytics Integration

    Central integration point for every analytics
    subsystem within Heshly.

    Other modules should only interact with this class
    instead of individual analytics services.
    """

    def __init__(self):

        self.analytics = AnalyticsManager()

        self.dashboard = DashboardManager()

        self.appointments = (
            AppointmentAnalyticsManager()
        )

        self.customers = (
            CustomerAnalyticsManager()
        )

        self.sales = (
            SalesAnalyticsManager()
        )

        self.ai = (
            AIAnalyticsManager()
        )

        self.marketing = (
            MarketingAnalyticsManager()
        )

        self.reporting = ReportManager()

        self.business_intelligence = BIManager()

    # =====================================================
    # Managers
    # =====================================================

    def managers(self) -> dict:

        return {

            "analytics":
                self.analytics,

            "dashboard":
                self.dashboard,

            "appointments":
                self.appointments,

            "customers":
                self.customers,

            "sales":
                self.sales,

            "ai":
                self.ai,

            "marketing":
                self.marketing,

            "reporting":
                self.reporting,

            "business_intelligence":
                self.business_intelligence,

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        services = {}

        services["analytics"] = (
            self.analytics.health()
        )

        services["dashboard"] = (
            self.dashboard.health()
        )

        services["appointments"] = (
            self.appointments.health()
        )

        services["customers"] = (
            self.customers.health()
        )

        services["sales"] = (
            self.sales.health()
        )

        services["ai"] = (
            self.ai.health()
        )

        services["marketing"] = (
            self.marketing.health()
        )

        services["reporting"] = (
            self.reporting.health()
        )

        services["business_intelligence"] = (
            self.business_intelligence.health()
        )

        return {

            "status": "healthy",

            "module": "Analytics",

            "services": services,

            "service_count": len(services),

        }

    # =====================================================
    # Summary
    # =====================================================

    def summary(self) -> dict:

        return {

            "analytics": True,

            "dashboard": True,

            "appointment_analytics": True,

            "customer_analytics": True,

            "sales_analytics": True,

            "ai_analytics": True,

            "marketing_analytics": True,

            "reporting_engine": True,

            "business_intelligence": True,

        }
        