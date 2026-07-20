from heshly_core.services.subscription.pricing_plans import (
    PricingPlans,
)


def run_test():

    print("\n==============================")
    print("Pricing Plans Test")
    print("==============================\n")

    starter = PricingPlans.starter()

    assert starter.name == "Starter"

    print("✅ Starter plan passed")

    growth = PricingPlans.growth()

    assert growth.max_users == 20

    print("✅ Growth plan passed")

    enterprise = PricingPlans.enterprise()

    assert enterprise.max_users > growth.max_users

    print("✅ Enterprise plan passed")

    plans = PricingPlans.all()

    assert len(plans) == 3

    print("✅ Plan catalog passed")

    found = PricingPlans.by_id("growth")

    assert found is not None

    assert found.name == "Growth"

    print("✅ Plan lookup passed")

    print("\n🎉 PRICING PLANS TEST PASSED\n")


if __name__ == "__main__":

    run_test()