from heshly_core.models.subscription import (
    Subscription,
)

from heshly_core.services.subscription.pricing_plans import (
    PricingPlans,
)

from heshly_core.services.subscription.subscription_limits import (
    SubscriptionLimits,
)


def run_test():

    print("\n==============================")
    print("Subscription Limits Test")
    print("==============================\n")

    subscription = Subscription(

        subscription_id="sub_001",

        tenant_id="tenant_001",

        plan=PricingPlans.starter(),

    )

    assert SubscriptionLimits.can_add_user(
        subscription,
        4,
    )

    print("✅ User limit passed")

    assert not SubscriptionLimits.can_add_user(
        subscription,
        5,
    )

    print("✅ User limit enforcement passed")

    assert SubscriptionLimits.can_add_business(
        subscription,
        0,
    )

    print("✅ Business limit passed")

    assert not SubscriptionLimits.can_add_business(
        subscription,
        1,
    )

    print("✅ Business limit enforcement passed")

    assert SubscriptionLimits.can_use_ai(
        subscription,
        500,
    )

    print("✅ AI usage passed")

    assert not SubscriptionLimits.can_use_ai(
        subscription,
        1000,
    )

    print("✅ AI limit enforcement passed")

    assert SubscriptionLimits.can_store(
        subscription,
        1024,
    )

    print("✅ Storage usage passed")

    assert not SubscriptionLimits.can_store(
        subscription,
        2048,
    )

    print("✅ Storage limit enforcement passed")

    summary = SubscriptionLimits.summary(
        subscription,
    )

    assert summary["plan"] == "Starter"

    print("✅ Summary passed")

    assert (
        SubscriptionLimits.health()["status"]
        == "healthy"
    )

    print("✅ Health check passed")

    print("\n🎉 SUBSCRIPTION LIMITS TEST PASSED\n")


if __name__ == "__main__":

    run_test()