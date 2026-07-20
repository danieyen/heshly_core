from heshly_core.models.subscription import (
    Subscription,
)

from heshly_core.services.subscription.pricing_plans import (
    PricingPlans,
)

from heshly_core.services.subscription.subscription_manager import (
    SubscriptionManager,
)


def run_test():

    print("\n==============================")
    print("Subscription Manager Test")
    print("==============================\n")

    manager = SubscriptionManager()

    starter = PricingPlans.starter()

    growth = PricingPlans.growth()

    subscription = Subscription(

        subscription_id="sub_001",

        tenant_id="tenant_001",

        plan=starter,

    )

    manager.create(
        subscription,
    )

    print("✅ Subscription creation passed")

    manager.activate(
        "sub_001",
    )

    assert manager.get(
        "sub_001",
    ).is_active

    print("✅ Activation passed")

    manager.change_plan(
        "sub_001",
        growth,
    )

    assert (
        manager.get(
            "sub_001",
        ).plan.name
        ==
        "Growth"
    )

    print("✅ Plan upgrade passed")

    assert manager.has_feature(
        "sub_001",
        "Analytics",
    )

    print("✅ Feature entitlement passed")

    manager.cancel(
        "sub_001",
    )

    assert (
        manager.get(
            "sub_001",
        ).status.value
        ==
        "cancelled"
    )

    print("✅ Cancellation passed")

    assert (
        manager.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health check passed")

    print("\n🎉 SUBSCRIPTION MANAGER TEST PASSED\n")


if __name__ == "__main__":

    run_test()