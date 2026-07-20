from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime


class ROIAnalytics:
    """
    Marketing ROI Analytics

    Expected campaign format

    {
        "campaign_id": "CMP-001",
        "campaign_name": "Facebook July",
        "channel": "Facebook",

        "spend": 25000,
        "revenue": 180000,

        "leads": 120,
        "customers": 18,

        "appointments": 42
    }
    """

    # =====================================================
    # Analyze
    # =====================================================

    def analyze(
        self,
        campaigns: list[dict],
    ) -> dict:

        campaign_results = {}

        channel_summary = defaultdict(
            lambda: {
                "spend": 0.0,
                "revenue": 0.0,
                "campaigns": 0,
            }
        )

        total_spend = 0.0
        total_revenue = 0.0

        for campaign in campaigns:

            campaign_id = campaign.get(
                "campaign_id",
                "UNKNOWN",
            )

            channel = campaign.get(
                "channel",
                "Unknown",
            )

            spend = float(
                campaign.get(
                    "spend",
                    0,
                )
            )

            revenue = float(
                campaign.get(
                    "revenue",
                    0,
                )
            )

            leads = int(
                campaign.get(
                    "leads",
                    0,
                )
            )

            customers = int(
                campaign.get(
                    "customers",
                    0,
                )
            )

            appointments = int(
                campaign.get(
                    "appointments",
                    0,
                )
            )

            profit = revenue - spend

            roi = (
                (profit / spend) * 100
                if spend
                else 0.0
            )

            roas = (
                revenue / spend
                if spend
                else 0.0
            )

            cost_per_lead = (
                spend / leads
                if leads
                else 0.0
            )

            cost_per_customer = (
                spend / customers
                if customers
                else 0.0
            )

            cost_per_appointment = (
                spend / appointments
                if appointments
                else 0.0
            )

            campaign_results[campaign_id] = {

                "campaign_name": campaign.get(
                    "campaign_name",
                    campaign_id,
                ),

                "channel": channel,

                "spend": round(
                    spend,
                    2,
                ),

                "revenue": round(
                    revenue,
                    2,
                ),

                "profit": round(
                    profit,
                    2,
                ),

                "roi": round(
                    roi,
                    2,
                ),

                "roas": round(
                    roas,
                    2,
                ),

                "cost_per_lead": round(
                    cost_per_lead,
                    2,
                ),

                "cost_per_customer": round(
                    cost_per_customer,
                    2,
                ),

                "cost_per_appointment": round(
                    cost_per_appointment,
                    2,
                ),

            }

            channel_summary[channel]["spend"] += spend
            channel_summary[channel]["revenue"] += revenue
            channel_summary[channel]["campaigns"] += 1

            total_spend += spend
            total_revenue += revenue

        channels = {}

        for channel, values in channel_summary.items():

            spend = values["spend"]
            revenue = values["revenue"]

            profit = revenue - spend

            roi = (
                (profit / spend) * 100
                if spend
                else 0.0
            )

            roas = (
                revenue / spend
                if spend
                else 0.0
            )

            channels[channel] = {

                "campaigns": values[
                    "campaigns"
                ],

                "spend": round(
                    spend,
                    2,
                ),

                "revenue": round(
                    revenue,
                    2,
                ),

                "profit": round(
                    profit,
                    2,
                ),

                "roi": round(
                    roi,
                    2,
                ),

                "roas": round(
                    roas,
                    2,
                ),

            }

        overall_profit = (
            total_revenue -
            total_spend
        )

        overall_roi = (
            (
                overall_profit /
                total_spend
            )
            * 100
            if total_spend
            else 0.0
        )

        overall_roas = (
            total_revenue /
            total_spend
            if total_spend
            else 0.0
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "campaigns": campaign_results,

            "channels": channels,

            "total_campaigns": len(
                campaign_results
            ),

            "total_spend": round(
                total_spend,
                2,
            ),

            "total_revenue": round(
                total_revenue,
                2,
            ),

            "total_profit": round(
                overall_profit,
                2,
            ),

            "overall_roi": round(
                overall_roi,
                2,
            ),

            "overall_roas": round(
                overall_roas,
                2,
            ),

        }

    # =====================================================
    # Rankings
    # =====================================================

    def best_campaigns(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report["campaigns"].items(),

            key=lambda item: item[1]["roi"],

            reverse=True,

        )[:limit]

    def best_channels(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report["channels"].items(),

            key=lambda item: item[1]["roi"],

            reverse=True,

        )[:limit]

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ):

        return {

            "campaigns": report[
                "total_campaigns"
            ],

            "marketing_spend": report[
                "total_spend"
            ],

            "revenue": report[
                "total_revenue"
            ],

            "profit": report[
                "total_profit"
            ],

            "overall_roi": report[
                "overall_roi"
            ],

            "overall_roas": report[
                "overall_roas"
            ],

            "best_campaign": self.best_campaigns(
                report,
                1,
            ),

            "best_channel": self.best_channels(
                report,
                1,
            ),

        }