from heshly_core.models.usage import (
    UsageMetric,
)

from heshly_core.services.billing.usage_tracking_service import (
    UsageTrackingService,
)


def run_test():

    print("\n================================")
    print("Usage Tracking Service Test")
    print("================================\n")


    tracker = UsageTrackingService()


    tracker.track_message(
        "tenant001",
        5,
    )

    print("✅ Message usage tracked")


    tracker.track_ai_conversation(
        "tenant001",
        2,
    )

    print("✅ AI conversation tracked")


    tracker.track_appointment(
        "tenant001",
    )

    print("✅ Appointment tracked")


    tracker.track_lead(
        "tenant001",
        3,
    )

    print("✅ Lead tracked")


    records = tracker.repository.list()


    assert len(records) == 4


    print("✅ Usage records created")


    assert (

        records[0].tenant_id

        ==

        "tenant001"

    )


    print("✅ Tenant association")


    assert (

        tracker.health()["status"]

        ==

        "healthy"

    )


    print("✅ Health check")


    print(
        "\n🎉 USAGE TRACKING SERVICE TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()