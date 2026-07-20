from __future__ import annotations

from heshly_core.services.ai.decision_engine import DecisionEngine
from heshly_core.services.ai.intent_classifier import IntentClassifier
from heshly_core.services.conversation.conversation_manager import (
    ConversationManager,
)
from heshly_core.services.ai_analytics.ai_analytics_manager import (
    AIAnalyticsManager,
)
from heshly_core.services.business_intelligence.bi_manager import (
    BIManager,
)


class AIAnalyticsIntegration:
    """
    AI Analytics Integration

    Connects the AI Engine with Analytics and
    Business Intelligence.

    Responsibilities
    ----------------
    • AI performance monitoring
    • Conversation analytics
    • Intent analytics
    • BI insights
    """

    def __init__(self):

        self.decision_engine = DecisionEngine()

        self.intent_classifier = IntentClassifier()

        self.conversations = ConversationManager()

        self.analytics = AIAnalyticsManager()

        self.business_intelligence = BIManager()

    # =====================================================
    # AI Snapshot
    # =====================================================

    def snapshot(self) -> dict:

        snapshot = {}

        if hasattr(self.decision_engine, "health"):
            snapshot["decision_engine"] = (
                self.decision_engine.health()
            )

        if hasattr(self.intent_classifier, "health"):
            snapshot["intent_classifier"] = (
                self.intent_classifier.health()
            )

        if hasattr(self.conversations, "health"):
            snapshot["conversation_manager"] = (
                self.conversations.health()
            )

        snapshot["analytics"] = (
            self.analytics.health()
        )

        snapshot["business_intelligence"] = (
            self.business_intelligence.health()
        )

        return snapshot

    # =====================================================
    # Dashboard
    # =====================================================

    def dashboard(self) -> dict:

        return {

            "module": "AI",

            "snapshot": self.snapshot(),

        }

    # =====================================================
    # AI Performance
    # =====================================================

    def performance(self) -> dict:

        analytics = (
            self.analytics.health()
        )

        bi = (
            self.business_intelligence.health()
        )

        return {

            "analytics": analytics,

            "business_intelligence": bi,

        }

    # =====================================================
    # Health
    # =====================================================

    def health(self) -> dict:

        return {

            "status": "healthy",

            "services": {

                "decision_engine": (
                    self.decision_engine.health()
                    if hasattr(
                        self.decision_engine,
                        "health",
                    )
                    else {"status": "unknown"}
                ),

                "intent_classifier": (
                    self.intent_classifier.health()
                    if hasattr(
                        self.intent_classifier,
                        "health",
                    )
                    else {"status": "unknown"}
                ),

                "conversation_manager": (
                    self.conversations.health()
                    if hasattr(
                        self.conversations,
                        "health",
                    )
                    else {"status": "unknown"}
                ),

                "ai_analytics": (
                    self.analytics.health()
                ),

                "business_intelligence": (
                    self.business_intelligence.health()
                ),

            },

        }