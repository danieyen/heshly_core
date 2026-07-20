from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from statistics import mean


class ConversationAnalytics:
    """
    Conversation Analytics

    Expected conversation format

    {
        "session_id": "...",
        "customer_id": "...",
        "started_at": datetime(...),
        "ended_at": datetime(...),
        "messages": 12,
        "user_messages": 6,
        "ai_messages": 6,
        "resolved": True,
        "handed_to_human": False,
        "booking_created": True,
        "sentiment": "positive",
        "channel": "whatsapp"
    }
    """

    # =====================================================
    # Analyze
    # =====================================================

    def analyze(
        self,
        conversations: list[dict],
    ) -> dict:

        durations = []
        message_counts = []

        resolved = 0
        unresolved = 0
        handovers = 0
        bookings = 0

        sentiment_breakdown = Counter()
        channel_breakdown = Counter()

        for conversation in conversations:

            started = conversation.get(
                "started_at"
            )

            ended = conversation.get(
                "ended_at"
            )

            if (
                isinstance(started, datetime)
                and isinstance(ended, datetime)
            ):

                durations.append(
                    (
                        ended - started
                    ).total_seconds()
                )

            messages = int(
                conversation.get(
                    "messages",
                    0,
                )
            )

            message_counts.append(messages)

            if conversation.get(
                "resolved",
                False,
            ):
                resolved += 1
            else:
                unresolved += 1

            if conversation.get(
                "handed_to_human",
                False,
            ):
                handovers += 1

            if conversation.get(
                "booking_created",
                False,
            ):
                bookings += 1

            sentiment = conversation.get(
                "sentiment",
                "unknown",
            )

            channel = conversation.get(
                "channel",
                "unknown",
            )

            sentiment_breakdown[
                sentiment
            ] += 1

            channel_breakdown[
                channel
            ] += 1

        total = len(conversations)

        average_duration = (
            round(
                mean(durations),
                2,
            )
            if durations
            else 0.0
        )

        average_messages = (
            round(
                mean(message_counts),
                2,
            )
            if message_counts
            else 0.0
        )

        resolution_rate = (
            round(
                resolved / total * 100,
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

        booking_rate = (
            round(
                bookings / total * 100,
                2,
            )
            if total
            else 0.0
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "total_conversations": total,

            "resolved": resolved,

            "unresolved": unresolved,

            "handovers": handovers,

            "bookings": bookings,

            "average_duration_seconds": average_duration,

            "average_messages": average_messages,

            "resolution_rate": resolution_rate,

            "handover_rate": handover_rate,

            "booking_rate": booking_rate,

            "sentiment_breakdown": dict(
                sentiment_breakdown
            ),

            "channel_breakdown": dict(
                channel_breakdown
            ),

        }

    # =====================================================
    # Rankings
    # =====================================================

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

    def top_sentiments(
        self,
        report: dict,
        limit: int = 5,
    ):

        return sorted(

            report[
                "sentiment_breakdown"
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

            "conversations": report[
                "total_conversations"
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

            "average_duration_seconds": report[
                "average_duration_seconds"
            ],

            "average_messages": report[
                "average_messages"
            ],

            "top_channel": self.top_channels(
                report,
                1,
            ),

            "top_sentiment": self.top_sentiments(
                report,
                1,
            ),

        }