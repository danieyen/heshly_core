from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from statistics import mean


class PipelineAnalytics:
    """
    Sales Pipeline Analytics

    Expected opportunity format

    {
        "opportunity_id": "...",
        "customer_name": "...",
        "owner": "John",
        "stage": "Qualified",
        "value": 50000,
        "probability": 70,
        "status": "open",
        "created_at": datetime(...),
        "closed_at": datetime(...) | None
    }
    """

    # =====================================================
    # Analyze
    # =====================================================

    def analyze(
        self,
        opportunities: list[dict],
    ) -> dict:

        stage_breakdown = defaultdict(int)
        stage_value = defaultdict(float)
        owner_breakdown = defaultdict(float)
        status_breakdown = defaultdict(int)

        values = []
        weighted_pipeline = 0.0
        total_pipeline = 0.0

        won = 0
        lost = 0
        open_count = 0

        sales_cycle = []

        for opportunity in opportunities:

            value = float(
                opportunity.get(
                    "value",
                    0,
                )
            )

            probability = float(
                opportunity.get(
                    "probability",
                    0,
                )
            )

            stage = opportunity.get(
                "stage",
                "Unknown",
            )

            owner = opportunity.get(
                "owner",
                "Unassigned",
            )

            status = opportunity.get(
                "status",
                "open",
            ).lower()

            stage_breakdown[stage] += 1
            stage_value[stage] += value
            owner_breakdown[owner] += value
            status_breakdown[status] += 1

            total_pipeline += value
            weighted_pipeline += (
                value * probability / 100
            )

            values.append(value)

            if status == "won":
                won += 1
            elif status == "lost":
                lost += 1
            else:
                open_count += 1

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
                sales_cycle.append(
                    (closed - created).days
                )

        total = len(opportunities)

        win_rate = (
            round(
                won / total * 100,
                2,
            )
            if total
            else 0.0
        )

        average_value = (
            round(
                mean(values),
                2,
            )
            if values
            else 0.0
        )

        average_cycle = (
            round(
                mean(sales_cycle),
                2,
            )
            if sales_cycle
            else 0.0
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "total_opportunities": total,

            "open": open_count,

            "won": won,

            "lost": lost,

            "win_rate": win_rate,

            "pipeline_value": round(
                total_pipeline,
                2,
            ),

            "weighted_pipeline": round(
                weighted_pipeline,
                2,
            ),

            "average_opportunity_value": average_value,

            "average_sales_cycle_days": average_cycle,

            "stage_breakdown": dict(
                stage_breakdown
            ),

            "stage_value": dict(
                stage_value
            ),

            "owner_breakdown": dict(
                owner_breakdown
            ),

            "status_breakdown": dict(
                status_breakdown
            ),

        }

    # =====================================================
    # Rankings
    # =====================================================

    def top_stages(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "stage_value"
            ].items(),

            key=lambda item: item[1],

            reverse=True,

        )[:limit]

    def top_owners(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "owner_breakdown"
            ].items(),

            key=lambda item: item[1],

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

            "opportunities": report[
                "total_opportunities"
            ],

            "pipeline_value": report[
                "pipeline_value"
            ],

            "weighted_pipeline": report[
                "weighted_pipeline"
            ],

            "win_rate": report[
                "win_rate"
            ],

            "average_value": report[
                "average_opportunity_value"
            ],

            "average_sales_cycle_days": report[
                "average_sales_cycle_days"
            ],

            "top_stage": self.top_stages(
                report,
                1,
            ),

            "top_owner": self.top_owners(
                report,
                1,
            ),

        }