from heshly_core.models.usage import (
    TenantUsage,
    UsageMetric,
)

from heshly_core.services.billing.usage_calculator import (
    UsageCalculator,
)


def run_test():

    print("\n================================")
    print("Usage Calculator Test")
    print("================================\n")


    calculator = UsageCalculator()


    calculator.repository.save(

        TenantUsage(

            usage_id="usage001",

            tenant_id="tenant001",

            metric=UsageMetric.MESSAGES_SENT,

            quantity=500,

        )

    )


    calculator.repository.save(

        TenantUsage(

            usage_id="usage002",

            tenant_id="tenant001",

            metric=UsageMetric.AI_CONVERSATIONS,

            quantity=100,

        )

    )


    calculator.repository.save(

        TenantUsage(

            usage_id="usage003",

            tenant_id="tenant001",

            metric=UsageMetric.LEADS_GENERATED,

            quantity=25,

        )

    )


    print("✅ Usage records loaded")


    assert (
        calculator.messages_sent(
            "tenant001"
        )
        ==
        500
    )

    print("✅ Messages calculated")


    assert (
        calculator.ai_conversations(
            "tenant001"
        )
        ==
        100
    )

    print("✅ AI conversations calculated")


    summary = calculator.summary(
        "tenant001"
    )


    assert summary["leads_generated"] == 25


    print("✅ Summary generated")


    assert (
        calculator.health()["status"]
        ==
        "healthy"
    )


    print("✅ Health check")


    print(
        "\n🎉 USAGE CALCULATOR TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()