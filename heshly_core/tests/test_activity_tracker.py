from heshly_core.repositories.audit_repository import (
    AuditRepository,
)
from heshly_core.services.security.activity_tracker import (
    ActivityTracker,
)
from heshly_core.services.security.audit_service import (
    AuditService,
)


def run_test():

    print("\n================================")
    print("Activity Tracker Test")
    print("================================\n")

    repository = AuditRepository()

    audit_service = AuditService(
        repository
    )

    tracker = ActivityTracker(
        audit_service
    )

    tracker.customer_created(

        "tenant001",

        "user001",

        "CUST001",

    )

    print("✅ Customer created")

    tracker.customer_updated(

        "tenant001",

        "user001",

        "CUST001",

    )

    print("✅ Customer updated")

    tracker.appointment_booked(

        "tenant001",

        "user001",

        "APT001",

    )

    print("✅ Appointment booked")

    tracker.lead_created(

        "tenant001",

        "user001",

        "LEAD001",

    )

    print("✅ Lead created")

    tracker.ai_conversation(

        "tenant001",

        "SESSION001",

    )

    print("✅ AI conversation")

    tracker.suspicious_activity(

        "tenant001",

        "user001",

        "Multiple failed login attempts",

    )

    print("✅ Suspicious activity")

    assert len(
        audit_service.history()
    ) == 6

    print("✅ Audit history")

    assert (

        tracker.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 ACTIVITY TRACKER TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()