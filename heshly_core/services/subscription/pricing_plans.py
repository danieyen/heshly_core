from __future__ import annotations

from heshly_core.models.subscription import (
    SubscriptionPlan,
)


class PricingPlans:
    """
    Heshly pricing plans.

    Central catalog of all
    supported subscription plans.
    """

    @staticmethod
    def starter() -> SubscriptionPlan:

        return SubscriptionPlan(

            plan_id="starter",

            name="Starter",

            description="Perfect for small businesses.",

            monthly_price=15000,

            yearly_price=150000,

            max_users=5,

            max_businesses=1,

            max_ai_conversations=1000,

            max_storage_mb=2048,

            features=[
                "AI Receptionist",
                "Appointments",
                "CRM",
                "Calendar",
            ],
        )

    @staticmethod
    def growth() -> SubscriptionPlan:

        return SubscriptionPlan(

            plan_id="growth",

            name="Growth",

            description="For growing businesses.",

            monthly_price=30000,

            yearly_price=300000,

            max_users=20,

            max_businesses=3,

            max_ai_conversations=10000,

            max_storage_mb=10240,

            features=[
                "Everything in Starter",
                "Analytics",
                "Marketing",
                "Automation",
                "Multi-user",
            ],
        )

    @staticmethod
    def enterprise() -> SubscriptionPlan:

        return SubscriptionPlan(

            plan_id="enterprise",

            name="Enterprise",

            description="For large organizations.",

            monthly_price=0,

            yearly_price=0,

            max_users=999999,

            max_businesses=999999,

            max_ai_conversations=999999,

            max_storage_mb=999999,

            features=[
                "Unlimited Users",
                "Unlimited AI",
                "Business Intelligence",
                "Custom Integrations",
                "Priority Support",
                "Dedicated Infrastructure",
            ],
        )

    @classmethod
    def all(cls) -> list[SubscriptionPlan]:

        return [

            cls.starter(),

            cls.growth(),

            cls.enterprise(),

        ]

    @classmethod
    def by_id(
        cls,
        plan_id: str,
    ) -> SubscriptionPlan | None:

        for plan in cls.all():

            if plan.plan_id == plan_id:

                return plan

        return None

    @classmethod
    def summary(cls) -> dict:

        return {

            "plans": len(cls.all()),

            "available": [
                plan.name
                for plan in cls.all()
            ],

        }