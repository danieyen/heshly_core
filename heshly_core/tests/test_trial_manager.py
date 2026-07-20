from heshly_core.models.subscription import (
    Subscription,
    SubscriptionStatus,
)

from heshly_core.services.subscription.pricing_plans import (
    PricingPlans,
)

from heshly_core.services.subscription.trial_manager import (
    TrialManager,
)


def run_test():

    print("\n==============================")
    print("Trial Manager Test")
    print("==============================\n")

    manager = TrialManager()

    subscription = Subscription(

        subscription_id="sub_001",

        tenant_id="tenant_001",

        plan=PricingPlans.starter(),

    )

    manager.start_trial(subscription)

    assert (
        subscription.status
        ==
        SubscriptionStatus.TRIAL
    )

    print("✅ Trial started")

    assert manager.is_trial_active(
        subscription
    )

    print("✅ Trial validation passed")

    assert (
        manager.days_remaining(
            subscription
        )
        >= 13
    )

    print("✅ Remaining days calculation passed")

    manager.convert_to_paid(
        subscription
    )

    assert (
        subscription.status
        ==
        SubscriptionStatus.ACTIVE
    )

    print("✅ Trial conversion passed")

    manager.expire_trial(
        subscription
    )

    assert (
        subscription.status
        ==
        SubscriptionStatus.EXPIRED
    )

    print("✅ Trial expiration passed")

    assert (
        manager.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health check passed")

    print("\n🎉 TRIAL MANAGER TEST PASSED\n")


if __name__ == "__main__":

    run_test()