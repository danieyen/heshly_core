from heshly_core.models.usage import (
    TenantUsage,
    UsageMetric,
)

from heshly_core.repositories.usage_repository import (
    UsageRepository,
)


def run_test():

    print("\n================================")
    print("Usage Repository Test")
    print("================================\n")


    repository = UsageRepository()


    message_usage = TenantUsage(

        usage_id="usage001",

        tenant_id="tenant001",

        metric=UsageMetric.MESSAGES_SENT,

        quantity=100,

        period="2026-07",

    )


    ai_usage = TenantUsage(

        usage_id="usage002",

        tenant_id="tenant001",

        metric=UsageMetric.AI_CONVERSATIONS,

        quantity=25,

        period="2026-07",

    )


    repository.save(
        message_usage
    )

    repository.save(
        ai_usage
    )


    print("✅ Usage records saved")


    record = repository.get(
        "usage001"
    )


    assert record is not None

    assert record.quantity == 100


    print("✅ Usage retrieval")


    tenant_records = (
        repository.list_by_tenant(
            "tenant001"
        )
    )


    assert len(tenant_records) == 2


    print("✅ Tenant filtering")


    messages = (
        repository.list_by_metric(
            UsageMetric.MESSAGES_SENT
        )
    )


    assert len(messages) == 1


    print("✅ Metric filtering")


    assert repository.count() == 2


    print("✅ Count")


    assert (
        repository.health()["status"]
        ==
        "healthy"
    )


    print("✅ Health check")


    print(
        "\n🎉 USAGE REPOSITORY TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()