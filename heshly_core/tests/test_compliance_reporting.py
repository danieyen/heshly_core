from heshly_core.models.audit_log import (
    AuditEventType,
    AuditSeverity,
)
from heshly_core.repositories.audit_repository import (
    AuditRepository,
)
from heshly_core.services.security.audit_service import (
    AuditService,
)
from heshly_core.services.security.compliance_reporting import (
    ComplianceReporting,
)


def run_test():

    print("\n================================")
    print("Compliance Reporting Test")
    print("================================\n")

    repository = AuditRepository()

    audit = AuditService(
        repository
    )

    reporting = ComplianceReporting(
        repository
    )

    audit.log(

        tenant_id="tenant001",

        user_id="user001",

        event_type=AuditEventType.CREATE,

        action="create_customer",

        resource="customer",

    )

    audit.log(

        tenant_id="tenant001",

        user_id="user001",

        event_type=AuditEventType.UPDATE,

        action="update_customer",

        resource="customer",

    )

    audit.log(

        tenant_id="tenant001",

        user_id="user001",

        event_type=AuditEventType.SECURITY,

        action="failed_login",

        resource="authentication",

        severity=AuditSeverity.CRITICAL,

    )

    report = reporting.generate_report(
        tenant_id="tenant001"
    )

    assert report["total_events"] == 3
    print("✅ Total events")

    assert report["security_events"] == 1
    print("✅ Security events")

    assert report["failed_events"] == 1
    print("✅ Failed events")

    assert reporting.has_security_events(
        "tenant001"
    )

    print("✅ Security detection")

    assert reporting.has_failures(
        "tenant001"
    )

    print("✅ Failure detection")

    assert (

        reporting.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 COMPLIANCE REPORTING TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()