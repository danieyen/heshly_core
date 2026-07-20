from heshly_core.services.admin.admin_dashboard import (
    AdminDashboard,
)


def run_test():

    print("\n================================")
    print("Admin Dashboard Test")
    print("================================\n")


    dashboard = AdminDashboard()


    overview = dashboard.overview()


    assert "tenants" in overview

    print("✅ Tenant overview loaded")


    assert "system" in overview

    print("✅ System overview loaded")


    tenant_summary = (
        dashboard.tenant_summary()
    )


    assert "total" in tenant_summary

    print("✅ Tenant summary loaded")


    system_summary = (
        dashboard.system_summary()
    )


    assert "services" in system_summary

    print("✅ System summary loaded")


    assert (
        dashboard.health()["status"]
        ==
        "healthy"
    )


    print("✅ Dashboard health")


    print(
        "\n🎉 ADMIN DASHBOARD TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()