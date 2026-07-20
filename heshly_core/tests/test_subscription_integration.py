from heshly_core.models.subscription import (
    Subscription,
    SubscriptionStatus,
)

from heshly_core.services.subscription.pricing_plans import (
    PricingPlans,
)

from heshly_core.services.subscription.subscription_manager import (
    SubscriptionManager,
)

from heshly_core.services.subscription.subscription_lifecycle import (
    SubscriptionLifecycle,
)

from heshly_core.services.subscription.trial_manager import (
    TrialManager,
)

from heshly_core.services.subscription.upgrade_downgrade_flow import (
    UpgradeDowngradeFlow,
)

from heshly_core.services.subscription.subscription_limits import (
    SubscriptionLimits,
)

from heshly_core.services.subscription.feature_entitlements import (
    FeatureEntitlements,
)


def run_test():

    print("\n================================")
    print("Subscription Final Integration Test")
    print("================================\n")

    print("Loading Subscription Manager...")
    manager = SubscriptionManager()
    print("✅ Subscription Manager loaded")

    print("Loading Subscription Lifecycle...")
    lifecycle = SubscriptionLifecycle()
    print("✅ Subscription Lifecycle loaded")

    print("Loading Trial Manager...")
    trial = TrialManager()
    print("✅ Trial Manager loaded")

    print("Loading Upgrade / Downgrade Flow...")
    upgrades = UpgradeDowngradeFlow()
    print("✅ Upgrade / Downgrade Flow loaded")

    starter = PricingPlans.starter()
    growth = PricingPlans.growth()

    subscription = Subscription(

        subscription_id="sub_001",

        tenant_id="tenant_001",

        plan=starter,

    )

    print("\nTesting subscription creation...")

    manager.create(subscription)

    assert manager.get("sub_001") is not None

    print("✅ Subscription creation passed")

    print("\nTesting trial...")

    trial.start_trial(subscription)

    assert subscription.status == SubscriptionStatus.TRIAL

    assert trial.is_trial_active(subscription)

    print("✅ Trial passed")

    print("\nTesting activation...")

    lifecycle.activate(subscription)

    assert subscription.status == SubscriptionStatus.ACTIVE

    print("✅ Activation passed")

    print("\nTesting feature entitlement...")

    assert FeatureEntitlements.has_feature(
        subscription.plan,
        "CRM",
    )

    print("✅ Feature entitlement passed")

    print("\nTesting subscription limits...")

    assert SubscriptionLimits.can_add_user(
        subscription,
        2,
    )

    assert SubscriptionLimits.can_use_ai(
        subscription,
        500,
    )

    print("✅ Subscription limits passed")

    print("\nTesting upgrade...")

    upgrades.upgrade(
        subscription,
        growth,
    )

    assert subscription.plan.name == "Growth"

    print("✅ Upgrade passed")

    print("\nTesting downgrade...")

    upgrades.downgrade(
        subscription,
        starter,
    )

    assert subscription.plan.name == "Starter"

    print("✅ Downgrade passed")

    print("\nTesting suspension...")

    lifecycle.suspend(subscription)

    assert subscription.status == SubscriptionStatus.SUSPENDED

    print("✅ Suspension passed")

    print("\nTesting reactivation...")

    lifecycle.activate(subscription)

    assert subscription.status == SubscriptionStatus.ACTIVE

    print("✅ Reactivation passed")

    print("\nTesting cancellation...")

    lifecycle.cancel(subscription)

    assert subscription.status == SubscriptionStatus.CANCELLED

    print("✅ Cancellation passed")

    print("\nTesting manager summary...")

    summary = manager.summary()

    assert summary["subscriptions"] == 1

    print("✅ Manager summary passed")

    print("\nTesting health checks...")

    assert manager.health()["status"] == "healthy"
    assert lifecycle.health()["status"] == "healthy"
    assert trial.health()["status"] == "healthy"
    assert upgrades.health()["status"] == "healthy"
    assert SubscriptionLimits.health()["status"] == "healthy"

    print("✅ Health checks passed")

    print("\n========================================")
    print("🎉 SUBSCRIPTION MODULE TEST PASSED")
    print("========================================\n")


if __name__ == "__main__":

    run_test()