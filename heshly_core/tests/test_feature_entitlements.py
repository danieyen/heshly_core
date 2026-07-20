from heshly_core.services.subscription.feature_entitlements import (
    FeatureEntitlements,
)

from heshly_core.services.subscription.pricing_plans import (
    PricingPlans,
)


def run_test():

    print("\n==============================")
    print("Feature Entitlements Test")
    print("==============================\n")

    starter = PricingPlans.starter()

    assert FeatureEntitlements.has_feature(
        starter,
        "CRM",
    )

    print("✅ Starter CRM entitlement passed")

    assert not FeatureEntitlements.has_feature(
        starter,
        "Business Intelligence",
    )

    print("✅ Feature restriction passed")

    growth = PricingPlans.growth()

    assert FeatureEntitlements.has_feature(
        growth,
        "Analytics",
    )

    print("✅ Growth Analytics entitlement passed")

    enterprise = PricingPlans.enterprise()

    assert FeatureEntitlements.feature_count(
        enterprise
    ) > 0

    print("✅ Enterprise features passed")

    summary = FeatureEntitlements.summary(
        starter
    )

    assert summary["plan"] == "Starter"

    print("✅ Summary passed")

    assert (
        FeatureEntitlements.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health check passed")

    print("\n🎉 FEATURE ENTITLEMENTS TEST PASSED\n")


if __name__ == "__main__":

    run_test()