from __future__ import annotations

from heshly_core.models.subscription import (
    Subscription,
)


class SubscriptionLimits:
    """
    Subscription Limits.

    Enforces plan usage limits.

    Future:
        • API request limits
        • WhatsApp conversation limits
        • Workflow limits
        • Storage quotas
        • Custom enterprise limits
    """

    # =====================================================
    # Users
    # =====================================================

    @staticmethod
    def can_add_user(
        subscription: Subscription,
        current_users: int,
    ) -> bool:

        return (
            current_users
            < subscription.plan.max_users
        )

    # =====================================================
    # Businesses
    # =====================================================

    @staticmethod
    def can_add_business(
        subscription: Subscription,
        current_businesses: int,
    ) -> bool:

        return (
            current_businesses
            < subscription.plan.max_businesses
        )

    # =====================================================
    # AI Conversations
    # =====================================================

    @staticmethod
    def can_use_ai(
        subscription: Subscription,
        conversations_used: int,
    ) -> bool:

        return (
            conversations_used
            < subscription.plan.max_ai_conversations
        )

    # =====================================================
    # Storage
    # =====================================================

    @staticmethod
    def can_store(
        subscription: Subscription,
        storage_used_mb: int,
    ) -> bool:

        return (
            storage_used_mb
            < subscription.plan.max_storage_mb
        )

    # =====================================================
    # Summary
    # =====================================================

    @staticmethod
    def summary(
        subscription: Subscription,
    ) -> dict:

        plan = subscription.plan

        return {
            "plan": plan.name,
            "max_users": plan.max_users,
            "max_businesses": plan.max_businesses,
            "max_ai_conversations": plan.max_ai_conversations,
            "max_storage_mb": plan.max_storage_mb,
        }

    # =====================================================
    # Health
    # =====================================================

    @staticmethod
    def health() -> dict:

        return {
            "service": "subscription_limits",
            "status": "healthy",
        }