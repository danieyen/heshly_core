from heshly_core.models.subscription import (
    BillingCycle,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)


def run_test():

    print("\n==============================")
    print("Subscription Models Test")
    print("==============================\n")

    plan = SubscriptionPlan(

        plan_id="starter",

        name="Starter",

        monthly_price=15000,

        yearly_price=150000,

        max_users=5,

        features=[
            "CRM",
            "Calendar",
            "AI Receptionist",
        ],
    )

    assert plan.name == "Starter"

    print("✅ Plan creation passed")

    subscription = Subscription(

        subscription_id="sub_001",

        tenant_id="tenant_001",

        plan=plan,

        billing_cycle=BillingCycle.MONTHLY,

    )

    assert subscription.status == SubscriptionStatus.TRIAL

    print("✅ Default trial status passed")

    subscription.activate()

    assert subscription.is_active

    print("✅ Activation passed")

    subscription.suspend()

    assert (
        subscription.status
        ==
        SubscriptionStatus.SUSPENDED
    )

    print("✅ Suspension passed")

    subscription.cancel()

    assert (
        subscription.status
        ==
        SubscriptionStatus.CANCELLED
    )

    print("✅ Cancellation passed")

    print("\n🎉 SUBSCRIPTION MODELS TEST PASSED\n")


if __name__ == "__main__":

    run_test()