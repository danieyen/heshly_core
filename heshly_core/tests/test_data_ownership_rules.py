from dataclasses import dataclass

from heshly_core.services.tenant.data_ownership_rules import (
    DataOwnershipRules,
)


@dataclass
class Resource:

    tenant_id: str | None = None


def run_test():

    print("\n==============================")
    print("Data Ownership Rules Test")
    print("==============================\n")

    resource = Resource()

    DataOwnershipRules.assign_owner(
        resource,
        "tenant_001",
    )

    assert resource.tenant_id == "tenant_001"

    print("✅ Owner assignment passed")

    assert DataOwnershipRules.belongs_to_tenant(
        resource,
        "tenant_001",
    )

    print("✅ Ownership validation passed")

    DataOwnershipRules.require_owner(
        resource,
        "tenant_001",
    )

    print("✅ Ownership enforcement passed")

    DataOwnershipRules.transfer_owner(
        resource,
        "tenant_002",
    )

    assert resource.tenant_id == "tenant_002"

    print("✅ Ownership transfer passed")

    assert (
        DataOwnershipRules.owner(resource)
        == "tenant_002"
    )

    print("✅ Owner lookup passed")

    summary = DataOwnershipRules.summary()

    assert summary["ownership_model"] == "tenant_based"

    print("✅ Summary passed")

    assert (
        DataOwnershipRules.health()["status"]
        == "healthy"
    )

    print("✅ Health check passed")

    print("\n🎉 DATA OWNERSHIP RULES TEST PASSED\n")


if __name__ == "__main__":

    run_test()