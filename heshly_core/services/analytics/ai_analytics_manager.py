from __future__ import annotations

from datetime import UTC, datetime

from heshly_core.models.ai_analytics import (
    AIAnalyticsPeriod,
)
from heshly_core.services.analytics.intent_analytics import (
    IntentAnalytics,
)
from heshly_core.services.analytics.conversation_analytics import (
    ConversationAnalytics,
)
from heshly_core.services.analytics.response_quality_metrics import (
    ResponseQualityMetrics,
)
from heshly_core.services.analytics.ai_performance import (
    AIPerformance,
)
from heshly_core.services.analytics.ai_learning_metrics import (
    AILearningMetrics,
)


class AIAnalyticsManager:
    """
    AI Analytics Manager

    Coordinates all AI analytics modules.

    Modules
    -------
    • Intent Analytics
    • Conversation Analytics
    • Response Quality Metrics
    • AI Performance
    • AI Learning Metrics
    """

    def __init__(self):

        self.intent = IntentAnalytics()

        self.conversation = ConversationAnalytics()

        self.response_quality = (
            ResponseQualityMetrics()
        )

        self.performance = (
            AIPerformance()
        )

        self.learning = (
            AILearningMetrics()
        )

    # =====================================================
    # Individual Reports
    # =====================================================

    def intent_report(
        self,
        records: list[dict],
    ):

        return self.intent.analyze(
            records
        )

    def conversation_report(
        self,
        conversations: list[dict],
    ):

        return self.conversation.analyze(
            conversations
        )

    def response_quality_report(
        self,
        responses: list[dict],
    ):

        return self.response_quality.analyze(
            responses
        )

    def performance_report(
        self,
        sessions: list[dict],
    ):

        return self.performance.analyze(
            sessions
        )

    def learning_report(
        self,
        learning_records: list[dict],
    ):

        return self.learning.analyze(
            learning_records
        )

    # =====================================================
    # Complete Report
    # =====================================================

    def complete_report(
        self,
        business_id: str,
        intent_records: list[dict],
        conversations: list[dict],
        responses: list[dict],
        sessions: list[dict],
        learning_records: list[dict],
        period: AIAnalyticsPeriod = (
            AIAnalyticsPeriod.MONTHLY
        ),
    ) -> dict:

        intent = self.intent_report(
            intent_records
        )

        conversation = (
            self.conversation_report(
                conversations
            )
        )

        response_quality = (
            self.response_quality_report(
                responses
            )
        )

        performance = (
            self.performance_report(
                sessions
            )
        )

        learning = (
            self.learning_report(
                learning_records
            )
        )

        return {

            "generated_at": datetime.now(
                UTC
            ),

            "business_id": business_id,

            "period": period.value,

            "intent": intent,

            "conversation": conversation,

            "response_quality": response_quality,

            "performance": performance,

            "learning": learning,

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self):

        return {

            "status": "healthy",

            "modules": {

                "intent_analytics": True,

                "conversation_analytics": True,

                "response_quality_metrics": True,

                "ai_performance": True,

                "ai_learning_metrics": True,

            },

        }

    # =====================================================
    # Executive Summary
    # =====================================================

    def summary(
        self,
        report: dict,
    ) -> dict:

        intent = report["intent"]

        conversation = report[
            "conversation"
        ]

        quality = report[
            "response_quality"
        ]

        performance = report[
            "performance"
        ]

        learning = report[
            "learning"
        ]

        return {

            "business_id": report[
                "business_id"
            ],

            "period": report[
                "period"
            ],

            "total_intents": intent[
                "total_records"
            ],

            "total_conversations": conversation[
                "total_conversations"
            ],

            "total_responses": quality[
                "total_responses"
            ],

            "total_sessions": performance[
                "total_sessions"
            ],

            "resolution_rate": performance[
                "resolution_rate"
            ],

            "booking_rate": performance[
                "booking_rate"
            ],

            "average_confidence": performance[
                "average_confidence"
            ],

            "average_response_time_ms": quality[
                "average_response_time_ms"
            ],

            "acceptance_rate": learning[
                "acceptance_rate"
            ],

            "average_feedback_score": learning[
                "average_feedback_score"
            ],

            "health": self.health(),

        }