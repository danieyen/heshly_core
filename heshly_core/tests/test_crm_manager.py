from heshly_core.services.crm.crm_manager import (
    CRMManager,
)


def run():

    print("=" * 60)
    print(" HESHLY CRM MANAGER TEST")
    print("=" * 60)

    crm = CRMManager()

    health = crm.health()

    print("\nLoaded Components")

    for component, status in health.items():

        print(f"{component}: {status}")

        assert status is True

    print("\nRepository Summary")

    print(crm.repository_summary())

    print("\nCRM Summary")

    print(crm.summary())

    print("\n" + "=" * 60)
    print("✅ CRM MANAGER TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    run()