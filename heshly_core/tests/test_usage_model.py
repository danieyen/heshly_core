from heshly_core.models.usage import (
    TenantUsage,
    UsageMetric,
)


def run_test():

    print("\n================================")
    print("Tenant Usage Model Test")
    print("================================\n")


    usage = TenantUsage(

        usage_id="usage001",

        tenant_id="tenant001",

        metric=UsageMetric.MESSAGES_SENT,

        period="2026-07",

    )


    print("✅ Usage record created")


    usage.increment()

    usage.increment(5)


    assert usage.quantity == 6

    print("✅ Usage increment")


    assert (
        usage.metric
        ==
        UsageMetric.MESSAGES_SENT
    )

    print("✅ Metric validation")


    print(
        "\n🎉 TENANT USAGE MODEL TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()