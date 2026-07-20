from datetime import UTC, datetime

from heshly_core.models.subscription import (
    Subscription,
    SubscriptionStatus,
)

from heshly_core.services.subscription.pricing_plans import (
    PricingPlans,
)

from heshly_core.services.subscription.subscription_lifecycle import (
    SubscriptionLifecycle,
)


def run_test():

    print("\n==============================")
    print("Subscription Lifecycle Test")
    print("==============================\n")

    lifecycle = SubscriptionLifecycle()

    subscription = Subscription(

        subscription_id="sub_001",

        tenant_id="tenant_001",

        plan=PricingPlans.starter(),

    )

    lifecycle.activate(subscription)

    assert subscription.status == SubscriptionStatus.ACTIVE

    print("✅ Activation passed")

    lifecycle.mark_past_due(subscription)

    assert subscription.status == SubscriptionStatus.PAST_DUE

    print("✅ Past due passed")

    renewal = datetime.now(UTC)

    lifecycle.renew(
        subscription,
        renewal,
    )

    assert subscription.status == SubscriptionStatus.ACTIVE

    assert subscription.renewal_date == renewal

    print("✅ Renewal passed")

    lifecycle.suspend(subscription)

    assert subscription.status == SubscriptionStatus.SUSPENDED

    print("✅ Suspension passed")

    lifecycle.cancel(subscription)

    assert subscription.status == SubscriptionStatus.CANCELLED

    print("✅ Cancellation passed")

    lifecycle.expire(subscription)

    assert subscription.status == SubscriptionStatus.EXPIRED

    print("✅ Expiration passed")

    assert lifecycle.health()["status"] == "healthy"

    print("✅ Health check passed")

    print("\n🎉 SUBSCRIPTION LIFECYCLE TEST PASSED\n")


if __name__ == "__main__":

    run_test()