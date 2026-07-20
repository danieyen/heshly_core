from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from statistics import mean


class AIPerformance:
    """
    AI Performance Analytics

    Expected session format

    {
        "session_id": "...",
        "customer_id": "...",

        "duration_seconds": 185,

        "messages": 12,

        "user_messages": 6,

        "ai_messages": 6,

        "confidence_score": 0.94,

        "resolved": True,

        "handed_to_human": False,

        "booking_created": True,

        "response_time_ms": 620,

        "tokens_used": 1840,

        "cost": 0.037,

        "model": "gpt-5.5",

        "channel": "whatsapp"
    }
    """

    # =====================================================
    # Analyze
    # =====================================================

    def analyze(
        self,
        sessions: list[dict],
    ) -> dict:

        total_sessions = len(sessions)

        durations = []
        messages = []
        confidences = []
        response_times = []
        token_usage = []
        costs = []

        resolved = 0
        handovers = 0
        bookings = 0

        model_breakdown = Counter()
        channel_breakdown = Counter()

        for session in sessions:

            durations.append(
                float(
                    session.get(
                        "duration_seconds",
                        0,
                    )
                )
            )

            messages.append(
                int(
                    session.get(
                        "messages",
                        0,
                    )
                )
            )

            confidences.append(
                float(
                    session.get(
                        "confidence_score",
                        0,
                    )
                )
            )

            response_times.append(
                float(
                    session.get(
                        "response_time_ms",
                        0,
                    )
                )
            )

            token_usage.append(
                int(
                    session.get(
                        "tokens_used",
                        0,
                    )
                )
            )

            costs.append(
                float(
                    session.get(
                        "cost",
                        0,
                    )
                )
            )

            if session.get(
                "resolved",
                False,
            ):
                resolved += 1

            if session.get(
                "handed_to_human",
                False,
            ):
                handovers += 1

            if session.get(
                "booking_created",
                False,
            ):
                bookings += 1

            model_breakdown[
                session.get(
                    "model",
                    "unknown",
                )
            ] += 1

            channel_breakdown[
                session.get(
                    "channel",
                    "unknown",
                )
            ] += 1

        resolution_rate = (
            round(
                resolved /
                total_sessions *
                100,
                2,
            )
            if total_sessions
            else 0.0
        )

        handover_rate = (
            round(
                handovers /
                total_sessions *
                100,
                2,
            )
            if total_sessions
            else 0.0
        )

        booking_rate = (
            round(
                bookings /
                total_sessions *
                100,
                2,
            )
            if total_sessions
            else 0.0
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "total_sessions": total_sessions,

            "resolved_sessions": resolved,

            "escalated_sessions": handovers,

            "booking_sessions": bookings,

            "resolution_rate": resolution_rate,

            "handover_rate": handover_rate,

            "booking_rate": booking_rate,

            "average_duration_seconds": round(
                mean(durations),
                2,
            ) if durations else 0.0,

            "average_messages": round(
                mean(messages),
                2,
            ) if messages else 0.0,

            "average_confidence": round(
                mean(confidences),
                3,
            ) if confidences else 0.0,

            "average_response_time_ms": round(
                mean(response_times),
                2,
            ) if response_times else 0.0,

            "average_tokens": round(
                mean(token_usage),
                2,
            ) if token_usage else 0.0,

            "total_tokens": sum(
                token_usage
            ),

            "average_cost": round(
                mean(costs),
                4,
            ) if costs else 0.0,

            "total_cost": round(
                sum(costs),
                4,
            ),

            "model_breakdown": dict(
                model_breakdown
            ),

            "channel_breakdown": dict(
                channel_breakdown
            ),

        }

    # =====================================================
    # Rankings
    # =====================================================

    def most_used_models(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "model_breakdown"
            ].items(),

            key=lambda item: item[1],

            reverse=True,

        )[:limit]

    def most_used_channels(
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

            "sessions": report[
                "total_sessions"
            ],

            "resolution_rate": report[
                "resolution_rate"
            ],

            "handover_rate": report[
                "handover_rate"
            ],

            "booking_rate": report[
                "booking_rate"
            ],

            "average_confidence": report[
                "average_confidence"
            ],

            "average_response_time_ms": report[
                "average_response_time_ms"
            ],

            "average_duration_seconds": report[
                "average_duration_seconds"
            ],

            "total_tokens": report[
                "total_tokens"
            ],

            "total_cost": report[
                "total_cost"
            ],

            "most_used_model": self.most_used_models(
                report,
                1,
            ),

            "most_used_channel": self.most_used_channels(
                report,
                1,
            ),

        }