from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime


class IntentAnalytics:
    """
    Intent Analytics

    Expected record

    {
        "intent": "BOOK_APPOINTMENT",
        "confidence": 0.96,
        "successful": True
    }
    """

    # =====================================================
    # Analyze
    # =====================================================

    def analyze(
        self,
        records: list[dict],
    ) -> dict:

        grouped = defaultdict(
            lambda: {
                "count": 0,
                "confidence_total": 0.0,
                "success": 0,
                "failure": 0,
            }
        )

        total_records = len(records)

        for record in records:

            intent = record.get(
                "intent",
                "UNKNOWN",
            )

            confidence = float(
                record.get(
                    "confidence",
                    0.0,
                )
            )

            successful = bool(
                record.get(
                    "successful",
                    False,
                )
            )

            grouped[intent]["count"] += 1
            grouped[intent][
                "confidence_total"
            ] += confidence

            if successful:
                grouped[intent][
                    "success"
                ] += 1
            else:
                grouped[intent][
                    "failure"
                ] += 1

        summary = {}

        total_confidence = 0.0

        for intent, values in grouped.items():

            avg_confidence = (
                values["confidence_total"]
                / values["count"]
            )

            success_rate = (
                values["success"]
                / values["count"]
                * 100
            )

            total_confidence += values[
                "confidence_total"
            ]

            summary[intent] = {

                "count": values["count"],

                "average_confidence": round(
                    avg_confidence,
                    3,
                ),

                "successful": values[
                    "success"
                ],

                "failed": values[
                    "failure"
                ],

                "success_rate": round(
                    success_rate,
                    2,
                ),

            }

        average_confidence = (

            total_confidence /
            total_records

            if total_records

            else 0.0

        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "total_records": total_records,

            "average_confidence": round(
                average_confidence,
                3,
            ),

            "intent_breakdown": summary,

        }

    # =====================================================
    # Rankings
    # =====================================================

    def most_common(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "intent_breakdown"
            ].items(),

            key=lambda item: item[1]["count"],

            reverse=True,

        )[:limit]

    def highest_success(
        self,
        report: dict,
        minimum: int = 1,
    ):

        ranking = []

        for intent, values in report[
            "intent_breakdown"
        ].items():

            if values["count"] < minimum:
                continue

            ranking.append(

                (
                    intent,
                    values[
                        "success_rate"
                    ],
                )

            )

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

            "records": report[
                "total_records"
            ],

            "average_confidence": report[
                "average_confidence"
            ],

            "most_common_intent": self.most_common(
                report,
                1,
            ),

            "highest_success_intent": self.highest_success(
                report,
                1,
            )[:1],

        }