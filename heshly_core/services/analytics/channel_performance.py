from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime


class ChannelPerformance:
    """
    Marketing Channel Performance Analytics

    Expected record

    {
        "channel": "Facebook",
        "impressions": 25000,
        "reach": 18000,
        "clicks": 950,
        "conversions": 82,
        "leads": 74,
        "appointments": 31,
        "customers": 18,
        "revenue": 245000,
        "spend": 52000
    }
    """

    # =====================================================
    # Analyze
    # =====================================================

    def analyze(
        self,
        campaigns: list[dict],
    ) -> dict:

        channels = defaultdict(
            lambda: {
                "impressions": 0,
                "reach": 0,
                "clicks": 0,
                "conversions": 0,
                "leads": 0,
                "appointments": 0,
                "customers": 0,
                "revenue": 0.0,
                "spend": 0.0,
            }
        )

        for campaign in campaigns:

            channel = campaign.get(
                "channel",
                "Unknown",
            )

            data = channels[channel]

            data["impressions"] += int(
                campaign.get(
                    "impressions",
                    0,
                )
            )

            data["reach"] += int(
                campaign.get(
                    "reach",
                    0,
                )
            )

            data["clicks"] += int(
                campaign.get(
                    "clicks",
                    0,
                )
            )

            data["conversions"] += int(
                campaign.get(
                    "conversions",
                    0,
                )
            )

            data["leads"] += int(
                campaign.get(
                    "leads",
                    0,
                )
            )

            data["appointments"] += int(
                campaign.get(
                    "appointments",
                    0,
                )
            )

            data["customers"] += int(
                campaign.get(
                    "customers",
                    0,
                )
            )

            data["revenue"] += float(
                campaign.get(
                    "revenue",
                    0,
                )
            )

            data["spend"] += float(
                campaign.get(
                    "spend",
                    0,
                )
            )

        report = {}

        total_revenue = 0.0
        total_spend = 0.0
        total_impressions = 0
        total_clicks = 0

        for channel, data in channels.items():

            ctr = (
                data["clicks"]
                / data["impressions"]
                * 100
                if data["impressions"]
                else 0.0
            )

            conversion_rate = (
                data["conversions"]
                / data["clicks"]
                * 100
                if data["clicks"]
                else 0.0
            )

            cpc = (
                data["spend"]
                / data["clicks"]
                if data["clicks"]
                else 0.0
            )

            cpl = (
                data["spend"]
                / data["leads"]
                if data["leads"]
                else 0.0
            )

            cpa = (
                data["spend"]
                / data["customers"]
                if data["customers"]
                else 0.0
            )

            roi = (
                (
                    data["revenue"]
                    - data["spend"]
                )
                / data["spend"]
                * 100
                if data["spend"]
                else 0.0
            )

            roas = (
                data["revenue"]
                / data["spend"]
                if data["spend"]
                else 0.0
            )

            report[channel] = {

                "impressions": data["impressions"],

                "reach": data["reach"],

                "clicks": data["clicks"],

                "conversions": data["conversions"],

                "leads": data["leads"],

                "appointments": data["appointments"],

                "customers": data["customers"],

                "revenue": round(
                    data["revenue"],
                    2,
                ),

                "spend": round(
                    data["spend"],
                    2,
                ),

                "ctr": round(
                    ctr,
                    2,
                ),

                "conversion_rate": round(
                    conversion_rate,
                    2,
                ),

                "cpc": round(
                    cpc,
                    2,
                ),

                "cpl": round(
                    cpl,
                    2,
                ),

                "cpa": round(
                    cpa,
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

            total_revenue += data["revenue"]
            total_spend += data["spend"]
            total_impressions += data["impressions"]
            total_clicks += data["clicks"]

        overall_ctr = (
            total_clicks
            / total_impressions
            * 100
            if total_impressions
            else 0.0
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "total_channels": len(
                report
            ),

            "total_revenue": round(
                total_revenue,
                2,
            ),

            "total_spend": round(
                total_spend,
                2,
            ),

            "overall_ctr": round(
                overall_ctr,
                2,
            ),

            "channels": report,

        }

    # =====================================================
    # Rankings
    # =====================================================

    def top_roi(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(
            report["channels"].items(),
            key=lambda x: x[1]["roi"],
            reverse=True,
        )[:limit]

    def top_revenue(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(
            report["channels"].items(),
            key=lambda x: x[1]["revenue"],
            reverse=True,
        )[:limit]

    def top_ctr(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(
            report["channels"].items(),
            key=lambda x: x[1]["ctr"],
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

            "channels": report[
                "total_channels"
            ],

            "revenue": report[
                "total_revenue"
            ],

            "marketing_spend": report[
                "total_spend"
            ],

            "overall_ctr": report[
                "overall_ctr"
            ],

            "best_roi_channel": self.top_roi(
                report,
                1,
            ),

            "highest_revenue_channel": self.top_revenue(
                report,
                1,
            ),

            "highest_ctr_channel": self.top_ctr(
                report,
                1,
            ),

        }