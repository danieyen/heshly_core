from heshly_core.models.tenant import (
    Tenant,
    TenantStatus,
    TenantConfiguration,
)

from heshly_core.services.admin.tenant_analytics import (
    TenantAnalytics,
)


def run_test():

    print("\n================================")
    print("Tenant Analytics Test")
    print("================================\n")


    analytics = TenantAnalytics()


    dental = Tenant(

        tenant_id="tenant001",

        name="Smile Dental",

        configuration=TenantConfiguration(

            industry="Dental"

        )

    )


    logistics = Tenant(

        tenant_id="tenant002",

        name="Fast Logistics",

        status=TenantStatus.ACTIVE,

        configuration=TenantConfiguration(

            industry="Logistics"

        )

    )


    analytics.repository.save(
        dental
    )

    analytics.repository.save(
        logistics
    )


    print("✅ Tenants loaded")


    assert analytics.total_tenants() == 2

    print("✅ Total tenants")


    assert analytics.active_tenants() == 1

    print("✅ Active tenants")


    breakdown = analytics.status_breakdown()

    assert breakdown["trial"] == 1

    assert breakdown["active"] == 1

    print("✅ Status breakdown")


    industries = analytics.industry_breakdown()

    assert industries["Dental"] == 1

    assert industries["Logistics"] == 1

    print("✅ Industry breakdown")


    summary = analytics.summary()

    assert summary["total_tenants"] == 2

    print("✅ Summary generated")


    assert analytics.health()["status"] == "healthy"

    print("✅ Health check")


    print(
        "\n🎉 TENANT ANALYTICS TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()