from heshly_core.models.usage import (
    TenantUsage,
    UsageMetric,
)

from heshly_core.services.billing.billing_reports import (
    BillingReports,
)


def run_test():

    print("\n================================")
    print("Billing Reports Test")
    print("================================\n")


    reports = BillingReports()


    reports.repository.save(

        TenantUsage(

            usage_id="usage001",

            tenant_id="tenant001",

            metric=UsageMetric.MESSAGES_SENT,

            quantity=300,

        )

    )


    reports.repository.save(

        TenantUsage(

            usage_id="usage002",

            tenant_id="tenant001",

            metric=UsageMetric.AI_CONVERSATIONS,

            quantity=50,

        )

    )


    print("✅ Usage data loaded")


    report = reports.tenant_report(
        "tenant001"
    )


    assert report["messages_sent"] == 300

    print("✅ Tenant report generated")


    assert report["ai_conversations"] == 50

    print("✅ AI usage included")


    assert reports.usage_events_count() == 2

    print("✅ Usage event count")


    assert (
        reports.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health check")


    print(
        "\n🎉 BILLING REPORTS TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()