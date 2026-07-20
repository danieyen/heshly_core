from datetime import UTC, datetime, timedelta

from heshly_core.models.ai_analytics import (
    AIAnalyticsPeriod,
)
from heshly_core.services.analytics.ai_analytics_manager import (
    AIAnalyticsManager,
)


# ==========================================================
# Sample Data
# ==========================================================

def sample_intents():

    return [

        {
            "intent": "BOOK_APPOINTMENT",
            "confidence": 0.96,
            "successful": True,
        },

        {
            "intent": "BOOK_APPOINTMENT",
            "confidence": 0.91,
            "successful": True,
        },

        {
            "intent": "ASK_PRICE",
            "confidence": 0.89,
            "successful": True,
        },

        {
            "intent": "CANCEL_APPOINTMENT",
            "confidence": 0.82,
            "successful": False,
        },

        {
            "intent": "UNKNOWN",
            "confidence": 0.41,
            "successful": False,
        },

    ]


def sample_conversations():

    now = datetime.now(UTC)

    return [

        {
            "session_id": "S001",
            "customer_id": "C001",
            "started_at": now - timedelta(minutes=10),
            "ended_at": now - timedelta(minutes=5),
            "messages": 12,
            "user_messages": 6,
            "ai_messages": 6,
            "resolved": True,
            "handed_to_human": False,
            "booking_created": True,
            "sentiment": "positive",
            "channel": "whatsapp",
        },

        {
            "session_id": "S002",
            "customer_id": "C002",
            "started_at": now - timedelta(minutes=20),
            "ended_at": now - timedelta(minutes=8),
            "messages": 18,
            "user_messages": 9,
            "ai_messages": 9,
            "resolved": False,
            "handed_to_human": True,
            "booking_created": False,
            "sentiment": "neutral",
            "channel": "web",
        },

    ]


def sample_responses():

    return [

        {
            "response_id": "R001",
            "intent": "BOOK_APPOINTMENT",
            "confidence": 0.96,
            "response_time_ms": 640,
            "tokens": 210,
            "rating": 5,
            "successful": True,
            "hallucination": False,
            "fallback": False,
            "human_handover": False,
            "channel": "whatsapp",
        },

        {
            "response_id": "R002",
            "intent": "ASK_PRICE",
            "confidence": 0.92,
            "response_time_ms": 590,
            "tokens": 160,
            "rating": 4,
            "successful": True,
            "hallucination": False,
            "fallback": False,
            "human_handover": False,
            "channel": "web",
        },

        {
            "response_id": "R003",
            "intent": "UNKNOWN",
            "confidence": 0.48,
            "response_time_ms": 930,
            "tokens": 245,
            "rating": 2,
            "successful": False,
            "hallucination": True,
            "fallback": True,
            "human_handover": True,
            "channel": "whatsapp",
        },

    ]


def sample_sessions():

    return [

        {
            "session_id": "S001",
            "customer_id": "C001",
            "duration_seconds": 305,
            "messages": 12,
            "user_messages": 6,
            "ai_messages": 6,
            "confidence_score": 0.95,
            "resolved": True,
            "handed_to_human": False,
            "booking_created": True,
            "response_time_ms": 640,
            "tokens_used": 1450,
            "cost": 0.031,
            "model": "gpt-5.5",
            "channel": "whatsapp",
        },

        {
            "session_id": "S002",
            "customer_id": "C002",
            "duration_seconds": 615,
            "messages": 18,
            "user_messages": 9,
            "ai_messages": 9,
            "confidence_score": 0.83,
            "resolved": False,
            "handed_to_human": True,
            "booking_created": False,
            "response_time_ms": 870,
            "tokens_used": 2390,
            "cost": 0.052,
            "model": "gpt-5.5",
            "channel": "web",
        },

    ]


def sample_learning():

    return [

        {
            "session_id": "S001",
            "intent": "BOOK_APPOINTMENT",
            "confidence_before": 0.76,
            "confidence_after": 0.95,
            "feedback_score": 5,
            "accepted_response": True,
            "corrected_by_human": False,
            "retrained": True,
            "knowledge_update": True,
            "prompt_version": "v1",
            "model": "gpt-5.5",
        },

        {
            "session_id": "S002",
            "intent": "ASK_PRICE",
            "confidence_before": 0.71,
            "confidence_after": 0.88,
            "feedback_score": 4,
            "accepted_response": True,
            "corrected_by_human": False,
            "retrained": False,
            "knowledge_update": False,
            "prompt_version": "v1",
            "model": "gpt-5.5",
        },

        {
            "session_id": "S003",
            "intent": "UNKNOWN",
            "confidence_before": 0.34,
            "confidence_after": 0.55,
            "feedback_score": 2,
            "accepted_response": False,
            "corrected_by_human": True,
            "retrained": True,
            "knowledge_update": True,
            "prompt_version": "v2",
            "model": "gpt-5.5",
        },

    ]


# ==========================================================
# Functional Test
# ==========================================================

def main():

    print("=" * 70)
    print("AI ANALYTICS FUNCTIONAL TEST")
    print("=" * 70)

    manager = AIAnalyticsManager()

    intent_report = manager.intent_report(
        sample_intents()
    )
    print("✓ Intent Analytics")

    conversation_report = manager.conversation_report(
        sample_conversations()
    )
    print("✓ Conversation Analytics")

    response_report = manager.response_quality_report(
        sample_responses()
    )
    print("✓ Response Quality Metrics")

    performance_report = manager.performance_report(
        sample_sessions()
    )
    print("✓ AI Performance")

    learning_report = manager.learning_report(
        sample_learning()
    )
    print("✓ AI Learning Metrics")

    report = manager.complete_report(
        business_id="BIZ-001",
        intent_records=sample_intents(),
        conversations=sample_conversations(),
        responses=sample_responses(),
        sessions=sample_sessions(),
        learning_records=sample_learning(),
        period=AIAnalyticsPeriod.MONTHLY,
    )

    print("✓ Complete AI Analytics Report")

    summary = manager.summary(report)

    print("\nExecutive Summary")
    print("-" * 70)

    for key, value in summary.items():
        print(f"{key}: {value}")

    assert intent_report["total_records"] == 5
    assert conversation_report["total_conversations"] == 2
    assert response_report["total_responses"] == 3
    assert performance_report["total_sessions"] == 2
    assert learning_report["total_records"] == 3

    assert report["business_id"] == "BIZ-001"
    assert summary["health"]["status"] == "healthy"

    print("\n" + "=" * 70)
    print("✅ AI ANALYTICS FUNCTIONAL TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()