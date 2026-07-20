from heshly_core.models.audit_log import (
    AuditEventType,
    AuditSeverity,
)
from heshly_core.repositories.audit_repository import (
    AuditRepository,
)
from heshly_core.services.security.activity_tracker import (
    ActivityTracker,
)
from heshly_core.services.security.audit_service import (
    AuditService,
)
from heshly_core.services.security.compliance_reporting import (
    ComplianceReporting,
)


def run_test():

    print("\n================================")
    print("Audit Integration Test")
    print("================================\n")

    # =====================================================
    # Setup
    # =====================================================

    repository = AuditRepository()

    audit = AuditService(
        repository
    )

    tracker = ActivityTracker(
        audit
    )

    reporting = ComplianceReporting(
        repository
    )

    print("✅ Services initialized")

    # =====================================================
    # Authentication Events
    # =====================================================

    audit.login(
        tenant_id="tenant001",
        user_id="user001",
    )

    audit.logout(
        tenant_id="tenant001",
        user_id="user001",
    )

    audit.access_denied(
        tenant_id="tenant001",
        user_id="user001",
        resource="crm",
    )

    print("✅ Authentication events")

    # =====================================================
    # Business Activities
    # =====================================================

    tracker.customer_created(
        "tenant001",
        "user001",
        "CUST001",
    )

    tracker.customer_updated(
        "tenant001",
        "user001",
        "CUST001",
    )

    tracker.appointment_booked(
        "tenant001",
        "user001",
        "APT001",
    )

    tracker.lead_created(
        "tenant001",
        "user001",
        "LEAD001",
    )

    print("✅ Business activities")

    # =====================================================
    # Security Event
    # =====================================================

    audit.security_event(

        tenant_id="tenant001",

        user_id="user001",

        action="multiple_failed_logins",

        description="Multiple failed login attempts",

    )

    print("✅ Security event")

    # =====================================================
    # Generic Event
    # =====================================================

    audit.log(

        tenant_id="tenant001",

        user_id="user001",

        event_type=AuditEventType.UPDATE,

        action="update_configuration",

        resource="configuration",

        severity=AuditSeverity.INFO,

        description="Configuration updated",

    )

    print("✅ Generic event")

    # =====================================================
    # Repository
    # =====================================================

    assert repository.count() == 8

    print("✅ Repository count")

    assert len(
        repository.list_by_tenant(
            "tenant001"
        )
    ) == 8

    print("✅ Tenant query")

    assert len(
        repository.list_by_user(
            "user001"
        )
    ) == 8

    print("✅ User query")

    assert len(
        repository.list_security_events()
    ) == 1

    print("✅ Security query")

    assert len(
        repository.list_failures()
    ) == 2

    print("✅ Failure query")

    # =====================================================
    # Compliance
    # =====================================================

    report = reporting.generate_report(
        tenant_id="tenant001"
    )

    assert report["total_events"] == 8

    assert report["security_events"] == 1

    assert report["failed_events"] == 2

    print("✅ Compliance report")

    assert reporting.has_security_events(
        "tenant001"
    )

    assert reporting.has_failures(
        "tenant001"
    )

    print("✅ Compliance helpers")

    # =====================================================
    # Health
    # =====================================================

    assert (
        repository.health()["status"]
        ==
        "healthy"
    )

    assert (
        audit.health()["status"]
        ==
        "healthy"
    )

    assert (
        tracker.health()["status"]
        ==
        "healthy"
    )

    assert (
        reporting.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health checks")

    print(
        "\n🎉 AUDIT & COMPLIANCE TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()