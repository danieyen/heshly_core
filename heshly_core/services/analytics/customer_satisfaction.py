from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from statistics import mean


class CustomerSatisfaction:
    """
    Customer Satisfaction Analytics

    Calculates customer satisfaction metrics including:

    • Average Rating
    • Net Promoter Score (NPS)
    • CSAT
    • Rating Distribution
    • Feedback Sentiment
    • Service Ratings
    • Staff Ratings

    Expected feedback format

    {
        "customer_id": "...",
        "customer_name": "...",
        "rating": 5,                # 1-5
        "nps": 10,                  # 0-10
        "service_name": "...",
        "employee_name": "...",
        "sentiment": "positive"
    }
    """

    # =====================================================
    # Analyze
    # =====================================================

    def analyze(
        self,
        feedback: list[dict],
    ) -> dict:

        ratings = []
        nps_scores = []

        rating_distribution = Counter()
        sentiment_distribution = Counter()
        service_ratings = {}
        staff_ratings = {}

        promoters = 0
        passives = 0
        detractors = 0

        for item in feedback:

            rating = float(
                item.get(
                    "rating",
                    0,
                )
            )

            ratings.append(rating)

            rating_distribution[int(rating)] += 1

            sentiment = item.get(
                "sentiment",
                "unknown",
            ).lower()

            sentiment_distribution[sentiment] += 1

            # ------------------------------------------
            # NPS
            # ------------------------------------------

            nps = item.get("nps")

            if nps is not None:

                nps = int(nps)

                nps_scores.append(nps)

                if nps >= 9:
                    promoters += 1
                elif nps >= 7:
                    passives += 1
                else:
                    detractors += 1

            # ------------------------------------------
            # Service
            # ------------------------------------------

            service = item.get(
                "service_name",
                "Unknown",
            )

            service_ratings.setdefault(
                service,
                [],
            ).append(rating)

            # ------------------------------------------
            # Staff
            # ------------------------------------------

            employee = item.get(
                "employee_name",
                "Unknown",
            )

            staff_ratings.setdefault(
                employee,
                [],
            ).append(rating)

        average_rating = (
            round(mean(ratings), 2)
            if ratings
            else 0.0
        )

        csat = (
            round(
                (
                    len(
                        [
                            r
                            for r in ratings
                            if r >= 4
                        ]
                    )
                    / len(ratings)
                )
                * 100,
                2,
            )
            if ratings
            else 0.0
        )

        total_nps = (
            promoters
            + passives
            + detractors
        )

        nps_score = (
            round(
                (
                    (
                        promoters
                        - detractors
                    )
                    / total_nps
                )
                * 100,
                2,
            )
            if total_nps
            else 0.0
        )

        service_summary = {

            service: round(
                mean(values),
                2,
            )

            for service, values
            in service_ratings.items()

        }

        staff_summary = {

            employee: round(
                mean(values),
                2,
            )

            for employee, values
            in staff_ratings.items()

        }

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "responses": len(feedback),

            "average_rating": average_rating,

            "csat": csat,

            "nps": nps_score,

            "promoters": promoters,

            "passives": passives,

            "detractors": detractors,

            "rating_distribution": dict(
                rating_distribution
            ),

            "sentiment_distribution": dict(
                sentiment_distribution
            ),

            "service_ratings": service_summary,

            "staff_ratings": staff_summary,

        }

    # =====================================================
    # Rankings
    # =====================================================

    def top_services(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "service_ratings"
            ].items(),

            key=lambda x: x[1],

            reverse=True,

        )[:limit]

    def top_staff(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "staff_ratings"
            ].items(),

            key=lambda x: x[1],

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

            "responses": report[
                "responses"
            ],

            "average_rating": report[
                "average_rating"
            ],

            "csat": report["csat"],

            "nps": report["nps"],

            "promoters": report[
                "promoters"
            ],

            "detractors": report[
                "detractors"
            ],

            "top_service": self.top_services(
                report,
                1,
            ),

            "top_staff": self.top_staff(
                report,
                1,
            ),

        }