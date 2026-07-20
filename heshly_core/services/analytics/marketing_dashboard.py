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


class MarketingDashboard:
    """
    Marketing Dashboard

    Aggregates all marketing analytics into a single
    dashboard suitable for business owners and managers.
    """

    def __init__(self):

        self.lead_sources = (
            LeadSourceAnalytics()
        )

        self.channel_performance = (
            ChannelPerformance()
        )

        self.roi = ROIAnalytics()

        self.attribution = (
            CampaignAttribution()
        )

    # =====================================================
    # Individual Sections
    # =====================================================

    def lead_source_report(
        self,
        leads: list[dict],
    ) -> dict:

        return self.lead_sources.analyze(
            leads
        )

    def channel_report(
        self,
        campaigns: list[dict],
    ) -> dict:

        return self.channel_performance.analyze(
            campaigns
        )

    def roi_report(
        self,
        campaigns: list[dict],
    ) -> dict:

        return self.roi.analyze(
            campaigns
        )

    def attribution_report(
        self,
        conversions: list[dict],
    ) -> dict:

        return self.attribution.analyze(
            conversions
        )

    # =====================================================
    # Complete Dashboard
    # =====================================================

    def build_dashboard(
        self,
        business_id: str,
        leads: list[dict],
        campaigns: list[dict],
        conversions: list[dict],
    ) -> dict:

        lead_report = self.lead_source_report(
            leads
        )

        channel_report = self.channel_report(
            campaigns
        )

        roi_report = self.roi_report(
            campaigns
        )

        attribution_report = (
            self.attribution_report(
                conversions
            )
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "business_id": business_id,

            "lead_sources": lead_report,

            "channel_performance": channel_report,

            "roi": roi_report,

            "campaign_attribution": attribution_report,

        }

    # =====================================================
    # Executive Summary
    # =====================================================

    def executive_summary(
        self,
        dashboard: dict,
    ) -> dict:

        lead_summary = self.lead_sources.summary(
            dashboard["lead_sources"]
        )

        channel_summary = (
            self.channel_performance.summary(
                dashboard[
                    "channel_performance"
                ]
            )
        )

        roi_summary = self.roi.summary(
            dashboard["roi"]
        )

        attribution_summary = (
            self.attribution.summary(
                dashboard[
                    "campaign_attribution"
                ]
            )
        )

        return {

            "business_id": dashboard[
                "business_id"
            ],

            "generated_at": dashboard[
                "generated_at"
            ],

            "total_leads": lead_summary[
                "leads"
            ],

            "marketing_spend": roi_summary[
                "marketing_spend"
            ],

            "revenue": roi_summary[
                "revenue"
            ],

            "profit": roi_summary[
                "profit"
            ],

            "overall_roi": roi_summary[
                "overall_roi"
            ],

            "overall_roas": roi_summary[
                "overall_roas"
            ],

            "overall_ctr": channel_summary[
                "overall_ctr"
            ],

            "top_lead_source": lead_summary[
                "top_source"
            ],

            "best_roi_channel": channel_summary[
                "best_roi_channel"
            ],

            "best_campaign": roi_summary[
                "best_campaign"
            ],

            "best_first_touch": attribution_summary[
                "best_first_touch"
            ],

            "best_last_touch": attribution_summary[
                "best_last_touch"
            ],

        }

    # =====================================================
    # KPI Snapshot
    # =====================================================

    def kpis(
        self,
        dashboard: dict,
    ) -> dict:

        roi = dashboard["roi"]

        channels = dashboard[
            "channel_performance"
        ]

        leads = dashboard[
            "lead_sources"
        ]

        return {

            "marketing_spend": roi[
                "total_spend"
            ],

            "marketing_revenue": roi[
                "total_revenue"
            ],

            "profit": roi[
                "total_profit"
            ],

            "roi_percent": roi[
                "overall_roi"
            ],

            "roas": roi[
                "overall_roas"
            ],

            "lead_sources": leads[
                "total_sources"
            ],

            "total_leads": leads[
                "total_leads"
            ],

            "channels": channels[
                "total_channels"
            ],

            "overall_ctr": channels[
                "overall_ctr"
            ],

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "modules": {

                "lead_source_analytics": True,

                "channel_performance": True,

                "roi_analytics": True,

                "campaign_attribution": True,

                "marketing_dashboard": True,

            },

        }