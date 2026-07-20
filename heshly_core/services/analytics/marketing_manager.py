from __future__ import annotations

from datetime import UTC, datetime

from heshly_core.services.analytics.lead_source_analytics import (
    LeadSourceAnalytics,
)
from heshly_core.services.analytics.channel_performance import (
    ChannelPerformance,
)
from heshly_core.services.analytics.roi_analytics import (
    ROIAnalytics,
)
from heshly_core.services.analytics.campaign_attribution import (
    CampaignAttribution,
)
from heshly_core.services.analytics.marketing_dashboard import (
    MarketingDashboard,
)


class MarketingManager:
    """
    Marketing Analytics Manager

    Coordinates all marketing analytics services.

    Components
    ----------
    • Lead Source Analytics
    • Channel Performance
    • ROI Analytics
    • Campaign Attribution
    • Marketing Dashboard
    """

    def __init__(self):

        self.lead_sources = LeadSourceAnalytics()

        self.channel_performance = (
            ChannelPerformance()
        )

        self.roi = ROIAnalytics()

        self.attribution = (
            CampaignAttribution()
        )

        self.dashboard = (
            MarketingDashboard()
        )

    # =====================================================
    # Analytics
    # =====================================================

    def analyze_leads(
        self,
        leads: list[dict],
    ) -> dict:

        return self.lead_sources.analyze(
            leads
        )

    def analyze_channels(
        self,
        campaigns: list[dict],
    ) -> dict:

        return self.channel_performance.analyze(
            campaigns
        )

    def analyze_roi(
        self,
        campaigns: list[dict],
    ) -> dict:

        return self.roi.analyze(
            campaigns
        )

    def analyze_attribution(
        self,
        conversions: list[dict],
    ) -> dict:

        return self.attribution.analyze(
            conversions
        )

    # =====================================================
    # Dashboard
    # =====================================================

    def dashboard_report(
        self,
        business_id: str,
        leads: list[dict],
        campaigns: list[dict],
        conversions: list[dict],
    ) -> dict:

        return self.dashboard.build_dashboard(
            business_id=business_id,
            leads=leads,
            campaigns=campaigns,
            conversions=conversions,
        )

    # =====================================================
    # Complete Report
    # =====================================================

    def complete_report(
        self,
        business_id: str,
        leads: list[dict],
        campaigns: list[dict],
        conversions: list[dict],
    ) -> dict:

        dashboard = self.dashboard_report(
            business_id,
            leads,
            campaigns,
            conversions,
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "business_id": business_id,

            "lead_source_analytics":
                dashboard[
                    "lead_sources"
                ],

            "channel_performance":
                dashboard[
                    "channel_performance"
                ],

            "roi_analytics":
                dashboard[
                    "roi"
                ],

            "campaign_attribution":
                dashboard[
                    "campaign_attribution"
                ],

            "dashboard": dashboard,

            "executive_summary":
                self.dashboard.executive_summary(
                    dashboard
                ),

            "kpis":
                self.dashboard.kpis(
                    dashboard
                ),

            "health":
                self.health(),

        }

    # =====================================================
    # KPI Snapshot
    # =====================================================

    def kpis(
        self,
        report: dict,
    ) -> dict:

        return report["kpis"]

    # =====================================================
    # Executive Summary
    # =====================================================

    def executive_summary(
        self,
        report: dict,
    ) -> dict:

        return report[
            "executive_summary"
        ]

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "service": "MarketingManager",

            "modules": {

                "lead_source_analytics": True,

                "channel_performance": True,

                "roi_analytics": True,

                "campaign_attribution": True,

                "marketing_dashboard": True,

                "marketing_manager": True,

            },

        }