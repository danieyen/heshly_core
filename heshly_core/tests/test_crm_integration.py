from heshly_core.services.crm.crm_integration import (
    CRMIntegration,
)


def run():

    print("=" * 60)
    print(" HESHLY CRM INTEGRATION TEST")
    print("=" * 60)

    integration = CRMIntegration()

    print("\nHealth Check")

    health = integration.health()

    for key, value in health.items():

        print(f"{key}: {value}")

    print("\nRepository Summary")

    print(

        integration.repository_summary()

    )

    print("\nSystem Summary")

    print(

        integration.summary()

    )

    session = integration.start_conversation(

        conversation_id="CONV-001",

        business_id="BIZ-001",

    )

    assert session.business_id == "BIZ-001"

    print("\n✓ Conversation Integration")

    print("\n" + "=" * 60)

    print("✅ CRM INTEGRATION TEST PASSED")

    print("=" * 60)


if __name__ == "__main__":

    run()