from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime


class LeadSourceAnalytics:
    """
    Lead Source Analytics

    Expected lead format

    {
        "lead_id": "LEAD-001",
        "source": "Facebook",
        "status": "converted",
        "value": 12000,
        "cost": 350,
        "customer": True,
        "appointment": True,
        "won": True
    }
    """

    # =====================================================
    # Analyze
    # =====================================================

    def analyze(
        self,
        leads: list[dict],
    ) -> dict:

        totals = defaultdict(
            lambda: {
                "leads": 0,
                "appointments": 0,
                "customers": 0,
                "won": 0,
                "revenue": 0.0,
                "cost": 0.0,
            }
        )

        for lead in leads:

            source = lead.get(
                "source",
                "Unknown",
            )

            totals[source]["leads"] += 1

            totals[source]["revenue"] += float(
                lead.get(
                    "value",
                    0,
                )
            )

            totals[source]["cost"] += float(
                lead.get(
                    "cost",
                    0,
                )
            )

            if lead.get(
                "appointment",
                False,
            ):
                totals[source][
                    "appointments"
                ] += 1

            if lead.get(
                "customer",
                False,
            ):
                totals[source][
                    "customers"
                ] += 1

            if lead.get(
                "won",
                False,
            ):
                totals[source]["won"] += 1

        breakdown = {}

        total_revenue = 0.0
        total_cost = 0.0
        total_leads = 0

        for source, values in totals.items():

            leads_count = values["leads"]

            appointments = values[
                "appointments"
            ]

            customers = values[
                "customers"
            ]

            revenue = values[
                "revenue"
            ]

            cost = values["cost"]

            appointment_rate = (
                appointments /
                leads_count *
                100
                if leads_count
                else 0.0
            )

            customer_rate = (
                customers /
                leads_count *
                100
                if leads_count
                else 0.0
            )

            roi = (
                (
                    revenue - cost
                )
                / cost
                * 100
                if cost
                else 0.0
            )

            breakdown[source] = {

                "leads": leads_count,

                "appointments": appointments,

                "customers": customers,

                "won": values["won"],

                "revenue": round(
                    revenue,
                    2,
                ),

                "cost": round(
                    cost,
                    2,
                ),

                "appointment_rate": round(
                    appointment_rate,
                    2,
                ),

                "customer_rate": round(
                    customer_rate,
                    2,
                ),

                "roi": round(
                    roi,
                    2,
                ),

            }

            total_leads += leads_count
            total_revenue += revenue
            total_cost += cost

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "total_sources": len(
                breakdown
            ),

            "total_leads": total_leads,

            "total_revenue": round(
                total_revenue,
                2,
            ),

            "total_cost": round(
                total_cost,
                2,
            ),

            "lead_sources": breakdown,

        }

    # =====================================================
    # Rankings
    # =====================================================

    def top_sources(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "lead_sources"
            ].items(),

            key=lambda item: item[1][
                "leads"
            ],

            reverse=True,

        )[:limit]

    def highest_revenue(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "lead_sources"
            ].items(),

            key=lambda item: item[1][
                "revenue"
            ],

            reverse=True,

        )[:limit]

    def highest_roi(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "lead_sources"
            ].items(),

            key=lambda item: item[1][
                "roi"
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

            "sources": report[
                "total_sources"
            ],

            "leads": report[
                "total_leads"
            ],

            "revenue": report[
                "total_revenue"
            ],

            "marketing_cost": report[
                "total_cost"
            ],

            "top_source": self.top_sources(
                report,
                1,
            ),

            "highest_revenue_source": self.highest_revenue(
                report,
                1,
            ),

            "highest_roi_source": self.highest_roi(
                report,
                1,
            ),

        }