from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from statistics import mean


class WinLossAnalysis:
    """
    Win / Loss Analysis

    Expected opportunity format

    {
        "opportunity_id": "...",
        "customer_name": "...",
        "owner": "Alice",
        "stage": "Proposal",
        "status": "won",          # won / lost / open
        "value": 75000,
        "loss_reason": "Price",
        "created_at": datetime(...),
        "closed_at": datetime(...)
    }
    """

    # =====================================================
    # Analysis
    # =====================================================

    def analyze(
        self,
        opportunities: list[dict],
    ) -> dict:

        won = []
        lost = []

        loss_reasons = Counter()
        owner_results = defaultdict(
            lambda: {
                "won": 0,
                "lost": 0,
                "revenue": 0.0,
            }
        )

        stage_results = defaultdict(
            lambda: {
                "won": 0,
                "lost": 0,
            }
        )

        cycle_days = []

        for opportunity in opportunities:

            status = (
                opportunity.get(
                    "status",
                    "open",
                )
                .lower()
                .strip()
            )

            owner = opportunity.get(
                "owner",
                "Unassigned",
            )

            stage = opportunity.get(
                "stage",
                "Unknown",
            )

            value = float(
                opportunity.get(
                    "value",
                    0,
                )
            )

            created = opportunity.get(
                "created_at"
            )

            closed = opportunity.get(
                "closed_at"
            )

            if (
                isinstance(created, datetime)
                and isinstance(closed, datetime)
            ):
                cycle_days.append(
                    (closed - created).days
                )

            if status == "won":

                won.append(opportunity)

                owner_results[owner]["won"] += 1
                owner_results[owner][
                    "revenue"
                ] += value

                stage_results[stage]["won"] += 1

            elif status == "lost":

                lost.append(opportunity)

                owner_results[owner]["lost"] += 1
                stage_results[stage]["lost"] += 1

                reason = opportunity.get(
                    "loss_reason",
                    "Unknown",
                )

                loss_reasons[reason] += 1

        total_closed = len(won) + len(lost)

        win_rate = (
            round(
                len(won)
                / total_closed
                * 100,
                2,
            )
            if total_closed
            else 0.0
        )

        loss_rate = (
            round(
                len(lost)
                / total_closed
                * 100,
                2,
            )
            if total_closed
            else 0.0
        )

        average_cycle = (
            round(
                mean(cycle_days),
                2,
            )
            if cycle_days
            else 0.0
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "closed_opportunities": total_closed,

            "won": len(won),

            "lost": len(lost),

            "win_rate": win_rate,

            "loss_rate": loss_rate,

            "average_sales_cycle_days": average_cycle,

            "loss_reasons": dict(
                loss_reasons
            ),

            "owner_results": dict(
                owner_results
            ),

            "stage_results": dict(
                stage_results
            ),

            "won_value": round(
                sum(
                    float(
                        o.get(
                            "value",
                            0,
                        )
                    )
                    for o in won
                ),
                2,
            ),

            "lost_value": round(
                sum(
                    float(
                        o.get(
                            "value",
                            0,
                        )
                    )
                    for o in lost
                ),
                2,
            ),

        }

    # =====================================================
    # Rankings
    # =====================================================

    def top_loss_reasons(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "loss_reasons"
            ].items(),

            key=lambda item: item[1],

            reverse=True,

        )[:limit]

    def top_sales_people(
        self,
        report: dict,
        limit: int = 5,
    ):

        ranking = []

        for owner, stats in report[
            "owner_results"
        ].items():

            closed = (
                stats["won"]
                + stats["lost"]
            )

            rate = (
                round(
                    stats["won"]
                    / closed
                    * 100,
                    2,
                )
                if closed
                else 0.0
            )

            ranking.append(
                (
                    owner,
                    rate,
                    stats["revenue"],
                )
            )

        return sorted(
            ranking,
            key=lambda item: item[1],
            reverse=True,
        )[:limit]

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ) -> dict:

        return {

            "closed_opportunities": report[
                "closed_opportunities"
            ],

            "won": report["won"],

            "lost": report["lost"],

            "win_rate": report[
                "win_rate"
            ],

            "loss_rate": report[
                "loss_rate"
            ],

            "won_value": report[
                "won_value"
            ],

            "lost_value": report[
                "lost_value"
            ],

            "average_sales_cycle_days": report[
                "average_sales_cycle_days"
            ],

            "top_loss_reason": self.top_loss_reasons(
                report,
                1,
            ),

            "top_salesperson": self.top_sales_people(
                report,
                1,
            ),

        }