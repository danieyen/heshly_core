from __future__ import annotations

from heshly_core.services.crm.lead_manager import LeadManager
from heshly_core.services.crm.opportunity_manager import OpportunityManager
from heshly_core.services.crm.pipeline_manager import PipelineManager
from heshly_core.services.crm.activity_manager import ActivityManager
from heshly_core.services.sales_analytics.sales_manager import (
    SalesAnalyticsManager,
)
from heshly_core.services.customer_analytics.customer_analytics_manager import (
    CustomerAnalyticsManager,
)


class CRMAnalyticsIntegration:
    """
    CRM Analytics Integration

    Connects CRM components with the Analytics module.
    """

    def __init__(self):

        self.leads = LeadManager()

        self.opportunities = OpportunityManager()

        self.pipeline = PipelineManager()

        self.activities = ActivityManager()

        self.sales_analytics = SalesAnalyticsManager()

        self.customer_analytics = (
            CustomerAnalyticsManager()
        )

    # =====================================================
    # CRM Snapshot
    # =====================================================

    def snapshot(self) -> dict:

        return {

            "leads": len(
                self.leads.list()
            ),

            "opportunities": len(
                self.opportunities.list()
            ),

            "activities": len(
                self.activities.list()
            ),

            "pipeline": len(
                self.pipeline.list()
            ),

        }

    # =====================================================
    # Sales Dashboard
    # =====================================================

    def sales_dashboard(self) -> dict:

        return {

            "crm": self.snapshot(),

            "sales":

                self.sales_analytics.health(),

        }

    # =====================================================
    # Customer Dashboard
    # =====================================================

    def customer_dashboard(self) -> dict:

        return {

            "crm": self.snapshot(),

            "customers":

                self.customer_analytics.health(),

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "crm": {

                "lead_manager": True,

                "opportunity_manager": True,

                "pipeline_manager": True,

                "activity_manager": True,

            },

            "analytics": {

                "sales":

                    self.sales_analytics.health(),

                "customers":

                    self.customer_analytics.health(),

            },

        }