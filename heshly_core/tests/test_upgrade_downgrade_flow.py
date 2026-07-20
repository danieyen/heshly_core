from heshly_core.models.subscription import (
    Subscription,
)

from heshly_core.services.subscription.pricing_plans import (
    PricingPlans,
)

from heshly_core.services.subscription.upgrade_downgrade_flow import (
    UpgradeDowngradeFlow,
)


def run_test():

    print("\n==============================")
    print("Upgrade / Downgrade Flow Test")
    print("==============================\n")

    flow = UpgradeDowngradeFlow()

    starter = PricingPlans.starter()

    growth = PricingPlans.growth()

    subscription = Subscription(

        subscription_id="sub_001",

        tenant_id="tenant_001",

        plan=starter,

    )

    assert subscription.plan.name == "Starter"

    print("✅ Initial plan passed")

    flow.upgrade(
        subscription,
        growth,
    )

    assert subscription.plan.name == "Growth"

    print("✅ Upgrade passed")

    flow.downgrade(
        subscription,
        starter,
    )

    assert subscription.plan.name == "Starter"

    print("✅ Downgrade passed")

    summary = flow.summary(
        subscription,
    )

    assert summary["plan"] == "Starter"

    print("✅ Summary passed")

    assert flow.health()["status"] == "healthy"

    print("✅ Health check passed")

    print("\n🎉 UPGRADE / DOWNGRADE FLOW TEST PASSED\n")


if __name__ == "__main__":

    run_test()