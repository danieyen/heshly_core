from heshly_core.models.subscription import (
    Subscription,
    SubscriptionStatus,
)


def run_test():

    print("\n================================")
    print("Subscription Test")
    print("================================\n")


    subscription = Subscription(

        subscription_id="sub001",

        tenant_id="tenant001",

        plan="growth",

    )


    assert (
        subscription.status
        ==
        SubscriptionStatus.TRIAL
    )


    print(
        "✅ Trial subscription created"
    )


    subscription.activate()


    assert (
        subscription.status
        ==
        SubscriptionStatus.ACTIVE
    )


    print(
        "✅ Subscription activated"
    )


    subscription.suspend()


    assert (
        subscription.status
        ==
        SubscriptionStatus.SUSPENDED
    )


    print(
        "✅ Subscription suspended"
    )


    subscription.cancel()


    assert (
        subscription.status
        ==
        SubscriptionStatus.CANCELLED
    )


    print(
        "✅ Subscription cancelled"
    )


    print(
        "\n🎉 SUBSCRIPTION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()