from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime


class ConversionAnalytics:
    """
    Sales Conversion Analytics

    Expected opportunity format

    {
        "opportunity_id": "...",
        "lead_id": "...",
        "stage": "Qualified",
        "status": "won",          # open / won / lost
        "source": "Website",
        "owner": "Alice",
        "value": 25000
    }
    """

    # =====================================================
    # Analysis
    # =====================================================

    def analyze(
        self,
        opportunities: list[dict],
    ) -> dict:

        total = len(opportunities)

        won = 0
        lost = 0
        open_count = 0

        source_stats = defaultdict(
            lambda: {
                "total": 0,
                "won": 0,
                "lost": 0,
            }
        )

        owner_stats = defaultdict(
            lambda: {
                "total": 0,
                "won": 0,
                "lost": 0,
            }
        )

        stage_stats = defaultdict(
            lambda: {
                "total": 0,
                "won": 0,
                "lost": 0,
            }
        )

        for opportunity in opportunities:

            status = (
                opportunity.get(
                    "status",
                    "open",
                )
                .lower()
                .strip()
            )

            source = opportunity.get(
                "source",
                "Unknown",
            )

            owner = opportunity.get(
                "owner",
                "Unassigned",
            )

            stage = opportunity.get(
                "stage",
                "Unknown",
            )

            source_stats[source]["total"] += 1
            owner_stats[owner]["total"] += 1
            stage_stats[stage]["total"] += 1

            if status == "won":

                won += 1

                source_stats[source]["won"] += 1
                owner_stats[owner]["won"] += 1
                stage_stats[stage]["won"] += 1

            elif status == "lost":

                lost += 1

                source_stats[source]["lost"] += 1
                owner_stats[owner]["lost"] += 1
                stage_stats[stage]["lost"] += 1

            else:

                open_count += 1

        overall_rate = (
            round(
                won / total * 100,
                2,
            )
            if total
            else 0.0
        )

        # ---------------------------------------------
        # Conversion %
        # ---------------------------------------------

        def calculate_rates(stats):

            results = {}

            for key, value in stats.items():

                conversion = (
                    round(
                        value["won"]
                        / value["total"]
                        * 100,
                        2,
                    )
                    if value["total"]
                    else 0.0
                )

                results[key] = {

                    **value,

                    "conversion_rate": conversion,

                }

            return results

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "total_opportunities": total,

            "won": won,

            "lost": lost,

            "open": open_count,

            "overall_conversion_rate": overall_rate,

            "source_breakdown": calculate_rates(
                source_stats
            ),

            "owner_breakdown": calculate_rates(
                owner_stats
            ),

            "stage_breakdown": calculate_rates(
                stage_stats
            ),

        }

    # =====================================================
    # Rankings
    # =====================================================

    def best_sources(
        self,
        report: dict,
        minimum: int = 1,
    ):

        ranking = [

            (
                source,
                values["conversion_rate"],
            )

            for source, values

            in report[
                "source_breakdown"
            ].items()

            if values["total"] >= minimum

        ]

        return sorted(
            ranking,
            key=lambda item: item[1],
            reverse=True,
        )

    def best_owners(
        self,
        report: dict,
        minimum: int = 1,
    ):

        ranking = [

            (
                owner,
                values["conversion_rate"],
            )

            for owner, values

            in report[
                "owner_breakdown"
            ].items()

            if values["total"] >= minimum

        ]

        return sorted(
            ranking,
            key=lambda item: item[1],
            reverse=True,
        )

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ):

        return {

            "opportunities": report[
                "total_opportunities"
            ],

            "won": report["won"],

            "lost": report["lost"],

            "open": report["open"],

            "overall_conversion_rate": report[
                "overall_conversion_rate"
            ],

            "best_source": self.best_sources(
                report,
            )[:1],

            "best_owner": self.best_owners(
                report,
            )[:1],

        }