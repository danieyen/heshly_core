from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime


class CampaignAttribution:
    """
    Campaign Attribution Analytics

    Expected conversion record

    {
        "customer_id": "CUST-001",
        "conversion_value": 25000,

        "touchpoints": [
            "Facebook",
            "Google",
            "WhatsApp"
        ],

        "first_touch": "Facebook",
        "last_touch": "WhatsApp"
    }
    """

    # =====================================================
    # First Touch Attribution
    # =====================================================

    def first_touch(
        self,
        conversions: list[dict],
    ) -> dict:

        attribution = defaultdict(
            lambda: {
                "conversions": 0,
                "revenue": 0.0,
            }
        )

        for conversion in conversions:

            channel = conversion.get(
                "first_touch",
                "Unknown",
            )

            revenue = float(
                conversion.get(
                    "conversion_value",
                    0,
                )
            )

            attribution[channel][
                "conversions"
            ] += 1

            attribution[channel][
                "revenue"
            ] += revenue

        return dict(attribution)

    # =====================================================
    # Last Touch Attribution
    # =====================================================

    def last_touch(
        self,
        conversions: list[dict],
    ) -> dict:

        attribution = defaultdict(
            lambda: {
                "conversions": 0,
                "revenue": 0.0,
            }
        )

        for conversion in conversions:

            channel = conversion.get(
                "last_touch",
                "Unknown",
            )

            revenue = float(
                conversion.get(
                    "conversion_value",
                    0,
                )
            )

            attribution[channel][
                "conversions"
            ] += 1

            attribution[channel][
                "revenue"
            ] += revenue

        return dict(attribution)

    # =====================================================
    # Linear Attribution
    # =====================================================

    def linear(
        self,
        conversions: list[dict],
    ) -> dict:

        attribution = defaultdict(
            lambda: {
                "credit": 0.0,
                "revenue": 0.0,
            }
        )

        for conversion in conversions:

            revenue = float(
                conversion.get(
                    "conversion_value",
                    0,
                )
            )

            touchpoints = conversion.get(
                "touchpoints",
                [],
            )

            if not touchpoints:
                continue

            credit = (
                1 / len(touchpoints)
            )

            revenue_share = (
                revenue / len(touchpoints)
            )

            for channel in touchpoints:

                attribution[channel][
                    "credit"
                ] += credit

                attribution[channel][
                    "revenue"
                ] += revenue_share

        return {

            channel: {

                "credit": round(
                    values["credit"],
                    2,
                ),

                "revenue": round(
                    values["revenue"],
                    2,
                ),

            }

            for channel, values
            in attribution.items()

        }

    # =====================================================
    # Analyze
    # =====================================================

    def analyze(
        self,
        conversions: list[dict],
    ) -> dict:

        first = self.first_touch(
            conversions
        )

        last = self.last_touch(
            conversions
        )

        linear = self.linear(
            conversions
        )

        total_revenue = sum(

            float(
                conversion.get(
                    "conversion_value",
                    0,
                )
            )

            for conversion
            in conversions

        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "total_conversions": len(
                conversions
            ),

            "total_revenue": round(
                total_revenue,
                2,
            ),

            "first_touch": first,

            "last_touch": last,

            "linear": linear,

        }

    # =====================================================
    # Ranking
    # =====================================================

    def top_first_touch(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "first_touch"
            ].items(),

            key=lambda item: item[1][
                "revenue"
            ],

            reverse=True,

        )[:limit]

    def top_last_touch(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "last_touch"
            ].items(),

            key=lambda item: item[1][
                "revenue"
            ],

            reverse=True,

        )[:limit]

    def top_linear(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "linear"
            ].items(),

            key=lambda item: item[1][
                "revenue"
            ],

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

            "conversions": report[
                "total_conversions"
            ],

            "revenue": report[
                "total_revenue"
            ],

            "best_first_touch": self.top_first_touch(
                report,
                1,
            ),

            "best_last_touch": self.top_last_touch(
                report,
                1,
            ),

            "best_linear_channel": self.top_linear(
                report,
                1,
            ),

        }