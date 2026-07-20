from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from statistics import mean


class ResponseQualityMetrics:
    """
    AI Response Quality Metrics

    Expected record

    {
        "response_id": "...",
        "intent": "BOOK_APPOINTMENT",
        "confidence": 0.96,
        "response_time_ms": 740,
        "tokens": 182,
        "rating": 5,                  # Optional 1-5
        "successful": True,
        "hallucination": False,
        "fallback": False,
        "human_handover": False,
        "channel": "whatsapp"
    }
    """

    # =====================================================
    # Analyze
    # =====================================================

    def analyze(
        self,
        responses: list[dict],
    ) -> dict:

        total = len(responses)

        confidences = []
        response_times = []
        token_counts = []
        ratings = []

        successful = 0
        failed = 0
        hallucinations = 0
        fallbacks = 0
        handovers = 0

        intent_breakdown = Counter()
        channel_breakdown = Counter()

        for response in responses:

            confidence = float(
                response.get(
                    "confidence",
                    0.0,
                )
            )

            response_time = float(
                response.get(
                    "response_time_ms",
                    0.0,
                )
            )

            tokens = int(
                response.get(
                    "tokens",
                    0,
                )
            )

            confidences.append(confidence)
            response_times.append(response_time)
            token_counts.append(tokens)

            rating = response.get("rating")

            if rating is not None:
                ratings.append(float(rating))

            if response.get(
                "successful",
                False,
            ):
                successful += 1
            else:
                failed += 1

            if response.get(
                "hallucination",
                False,
            ):
                hallucinations += 1

            if response.get(
                "fallback",
                False,
            ):
                fallbacks += 1

            if response.get(
                "human_handover",
                False,
            ):
                handovers += 1

            intent_breakdown[
                response.get(
                    "intent",
                    "UNKNOWN",
                )
            ] += 1

            channel_breakdown[
                response.get(
                    "channel",
                    "unknown",
                )
            ] += 1

        success_rate = (
            round(
                successful / total * 100,
                2,
            )
            if total
            else 0.0
        )

        hallucination_rate = (
            round(
                hallucinations / total * 100,
                2,
            )
            if total
            else 0.0
        )

        fallback_rate = (
            round(
                fallbacks / total * 100,
                2,
            )
            if total
            else 0.0
        )

        handover_rate = (
            round(
                handovers / total * 100,
                2,
            )
            if total
            else 0.0
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "total_responses": total,

            "successful": successful,

            "failed": failed,

            "success_rate": success_rate,

            "average_confidence": round(
                mean(confidences),
                3,
            ) if confidences else 0.0,

            "average_response_time_ms": round(
                mean(response_times),
                2,
            ) if response_times else 0.0,

            "average_tokens": round(
                mean(token_counts),
                2,
            ) if token_counts else 0.0,

            "average_rating": round(
                mean(ratings),
                2,
            ) if ratings else 0.0,

            "hallucinations": hallucinations,

            "hallucination_rate": hallucination_rate,

            "fallbacks": fallbacks,

            "fallback_rate": fallback_rate,

            "human_handovers": handovers,

            "handover_rate": handover_rate,

            "intent_breakdown": dict(
                intent_breakdown
            ),

            "channel_breakdown": dict(
                channel_breakdown
            ),

        }

    # =====================================================
    # Rankings
    # =====================================================

    def top_intents(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "intent_breakdown"
            ].items(),

            key=lambda item: item[1],

            reverse=True,

        )[:limit]

    def top_channels(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "channel_breakdown"
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

            "responses": report[
                "total_responses"
            ],

            "success_rate": report[
                "success_rate"
            ],

            "average_confidence": report[
                "average_confidence"
            ],

            "average_response_time_ms": report[
                "average_response_time_ms"
            ],

            "average_tokens": report[
                "average_tokens"
            ],

            "average_rating": report[
                "average_rating"
            ],

            "hallucination_rate": report[
                "hallucination_rate"
            ],

            "fallback_rate": report[
                "fallback_rate"
            ],

            "handover_rate": report[
                "handover_rate"
            ],

            "top_intent": self.top_intents(
                report,
                1,
            ),

            "top_channel": self.top_channels(
                report,
                1,
            ),

        }