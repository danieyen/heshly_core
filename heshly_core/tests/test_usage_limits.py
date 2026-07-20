from heshly_core.models.usage import (
    TenantUsage,
    UsageMetric,
)

from heshly_core.services.billing.usage_limits import (
    UsageLimits,
)


def run_test():

    print("\n================================")
    print("Usage Limits Test")
    print("================================\n")


    limits = UsageLimits()


    limits.calculator.repository.save(

        TenantUsage(

            usage_id="usage001",

            tenant_id="tenant001",

            metric=UsageMetric.MESSAGES_SENT,

            quantity=800,

        )

    )


    print("✅ Usage loaded")


    limits.set_limit(

        UsageMetric.MESSAGES_SENT,

        1000,

    )


    print("✅ Limit configured")


    assert (

        not limits.exceeded(

            "tenant001",

            UsageMetric.MESSAGES_SENT,

        )

    )


    print("✅ Within limit")


    remaining = limits.remaining(

        "tenant001",

        UsageMetric.MESSAGES_SENT,

    )


    assert remaining == 200


    print("✅ Remaining calculated")


    limits.calculator.repository.save(

        TenantUsage(

            usage_id="usage002",

            tenant_id="tenant001",

            metric=UsageMetric.MESSAGES_SENT,

            quantity=500,

        )

    )


    assert limits.exceeded(

        "tenant001",

        UsageMetric.MESSAGES_SENT,

    )


    print("✅ Limit exceeded detection")


    assert (

        limits.health()["status"]

        ==

        "healthy"

    )


    print("✅ Health check")


    print(
        "\n🎉 USAGE LIMITS TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()