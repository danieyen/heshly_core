from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean


@dataclass(slots=True)
class Recommendation:

    title: str

    description: str

    priority: str

    category: str

    score: float

    actions: list[str] = field(
        default_factory=list
    )


class RecommendationEngine:
    """
    Business Intelligence Recommendation Engine

    Generates actionable business recommendations from
    KPIs, trends, anomalies, and benchmark comparisons.
    """

    def __init__(self):

        self.version = "1.0"

    # =====================================================
    # KPI Recommendations
    # =====================================================

    def from_kpis(
        self,
        kpis: dict[str, float],
    ) -> list[Recommendation]:

        recommendations = []

        revenue = kpis.get("revenue_growth", 0)

        if revenue < 0:

            recommendations.append(

                Recommendation(

                    title="Revenue Declining",

                    description=(
                        "Revenue growth is negative."
                    ),

                    priority="high",

                    category="sales",

                    score=95,

                    actions=[
                        "Review pricing",
                        "Increase marketing",
                        "Follow up lost leads",
                    ],

                )

            )

        conversion = kpis.get(
            "conversion_rate",
            100,
        )

        if conversion < 20:

            recommendations.append(

                Recommendation(

                    title="Improve Conversion",

                    description=(
                        "Lead conversion is below target."
                    ),

                    priority="high",

                    category="crm",

                    score=90,

                    actions=[
                        "Review sales funnel",
                        "Improve qualification",
                        "Increase follow-ups",
                    ],

                )

            )

        no_show = kpis.get(
            "no_show_rate",
            0,
        )

        if no_show > 15:

            recommendations.append(

                Recommendation(

                    title="Reduce No-Shows",

                    description=(
                        "Appointment no-show rate is high."
                    ),

                    priority="medium",

                    category="appointments",

                    score=80,

                    actions=[
                        "Send reminders",
                        "Require confirmation",
                        "Enable deposits",
                    ],

                )

            )

        return recommendations

    # =====================================================
    # Trend Recommendations
    # =====================================================

    def from_trends(
        self,
        trend_report: dict,
    ) -> list[Recommendation]:

        recommendations = []

        trend = trend_report.get(
            "trend",
            "stable",
        )

        growth = trend_report.get(
            "growth",
            0,
        )

        if trend == "decreasing":

            recommendations.append(

                Recommendation(

                    title="Negative Trend Detected",

                    description=(
                        "Business metrics are decreasing."
                    ),

                    priority="high",

                    category="performance",

                    score=88,

                    actions=[
                        "Investigate root cause",
                        "Review recent changes",
                    ],

                )

            )

        elif growth > 20:

            recommendations.append(

                Recommendation(

                    title="Rapid Growth",

                    description=(
                        "Prepare for increased demand."
                    ),

                    priority="medium",

                    category="operations",

                    score=75,

                    actions=[
                        "Increase capacity",
                        "Hire staff",
                    ],

                )

            )

        return recommendations

    # =====================================================
    # Anomaly Recommendations
    # =====================================================

    def from_anomalies(
        self,
        anomaly_report: dict,
    ) -> list[Recommendation]:

        if anomaly_report.get(
            "count",
            0,
        ) == 0:

            return []

        return [

            Recommendation(

                title="Business Anomalies Found",

                description=(
                    f"{anomaly_report['count']} "
                    "unusual values detected."
                ),

                priority="high",

                category="analytics",

                score=92,

                actions=[
                    "Review affected metrics",
                    "Validate data quality",
                    "Investigate causes",
                ],

            )

        ]

    # =====================================================
    # Benchmark Recommendations
    # =====================================================

    def from_benchmarks(
        self,
        benchmark_summary: dict,
    ) -> list[Recommendation]:

        recommendations = []

        score = benchmark_summary.get(
            "performance_score",
            100,
        )

        if score < 90:

            recommendations.append(

                Recommendation(

                    title="Below Benchmark",

                    description=(
                        "Business performance is below target."
                    ),

                    priority="medium",

                    category="benchmark",

                    score=85,

                    actions=[
                        "Review weak KPIs",
                        "Compare with industry",
                    ],

                )

            )

        return recommendations

    # =====================================================
    # Combined Recommendations
    # =====================================================

    def generate(
        self,
        kpis: dict | None = None,
        trends: dict | None = None,
        anomalies: dict | None = None,
        benchmarks: dict | None = None,
    ) -> list[Recommendation]:

        results = []

        if kpis:

            results.extend(
                self.from_kpis(kpis)
            )

        if trends:

            results.extend(
                self.from_trends(trends)
            )

        if anomalies:

            results.extend(
                self.from_anomalies(anomalies)
            )

        if benchmarks:

            results.extend(
                self.from_benchmarks(
                    benchmarks
                )
            )

        results.sort(
            key=lambda r: r.score,
            reverse=True,
        )

        return results

    # =====================================================
    # Summary
    # =====================================================

    def summary(
        self,
        recommendations: list[Recommendation],
    ) -> dict:

        if not recommendations:

            return {

                "count": 0,

                "average_score": 0,

                "highest_priority": None,

            }

        priorities = {
            "high": 3,
            "medium": 2,
            "low": 1,
        }

        highest = max(
            recommendations,
            key=lambda r: priorities.get(
                r.priority,
                0,
            ),
        )

        return {

            "count": len(
                recommendations
            ),

            "average_score": round(
                mean(
                    r.score
                    for r in recommendations
                ),
                2,
            ),

            "highest_priority":
                highest.priority,

            "top_recommendation":
                highest.title,

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "service":
                "RecommendationEngine",

            "version":
                self.version,

        }