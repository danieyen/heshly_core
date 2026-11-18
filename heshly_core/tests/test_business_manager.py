import frappe

from heshly_core.services.business.business_manager import (
    BusinessManager,
)

from heshly_core.services.tenant.tenant_context import (
    TenantContext,
)


def run_test():

    print("\n========================================")
    print("Business Manager / Frappe Test")
    print("========================================\n")

    context = TenantContext()
    manager = BusinessManager()

    context.set("heshly")

    print("context:", context.get())

    print(
        "repository:",
        manager.repository.__class__.__name__,
    )

    assert (
        manager.repository.__class__.__name__
        == "FrappeBusinessRepository"
    )

    print("✅ Frappe repository confirmed")

    business = manager.get("HESHLY")

    print("business:", business)

    assert business is not None
    assert business.business_id == "HESHLY"
    assert business.tenant_id == "heshly"
    assert business.name == "Heshly"
    assert business.status == "active"

    print("✅ Existing business retrieval passed")

    context.set("tenant_other")

    wrong_tenant = manager.get("HESHLY")

    print("wrong tenant result:", wrong_tenant)

    assert wrong_tenant is None

    print("✅ Manager tenant isolation passed")

    context.set("heshly")

    missing = manager.get("DOES_NOT_EXIST")

    assert missing is None

    print("✅ Missing business handling passed")

    try:
        manager.get("")
    except ValueError as e:
        print("missing ID:", e)
    else:
        raise AssertionError(
            "Expected ValueError for missing business_id"
        )

    print("✅ Missing business_id validation passed")

    health = manager.health()

    print("health:", health)

    assert health["status"] == "healthy"

    print("✅ Manager health passed")

    repository_health = manager.repository.health()

    print(
        "repository health:",
        repository_health,
    )

    assert repository_health["status"] == "healthy"
    assert repository_health["tenant"] is True

    print("✅ Repository health passed")

    context.clear()

    print()
    print("🎉 BUSINESS MANAGER / FRAPPE TEST PASSED")


if __name__ == "__main__":
    run_test()
