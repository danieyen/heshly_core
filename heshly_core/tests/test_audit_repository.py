from datetime import UTC, datetime, timedelta

from heshly_core.models.audit_log import (
    AuditEventType,
    AuditLog,
    AuditSeverity,
)

from heshly_core.repositories.audit_repository import (
    AuditRepository,
)


def run_test():

    print("\n================================")
    print("Audit Repository Test")
    print("================================\n")


    repository = AuditRepository()


    audit1 = AuditLog(

        audit_id="audit001",

        tenant_id="tenant001",

        user_id="user001",

        event_type=AuditEventType.UPDATE,

        action="update_customer",

        resource="customer",

    )


    audit2 = AuditLog(

        audit_id="audit002",

        tenant_id="tenant001",

        user_id="user002",

        event_type=AuditEventType.SECURITY,

        action="failed_login",

        resource="authentication",

        severity=AuditSeverity.ERROR,

    )


    repository.save(audit1)

    repository.save(audit2)


    assert repository.count() == 2

    print("✅ Saved audit logs")


    assert repository.get(
        "audit001"
    ) is not None

    print("✅ Retrieved by ID")


    assert len(
        repository.list_by_tenant(
            "tenant001"
        )
    ) == 2

    print("✅ Tenant filtering")


    assert len(
        repository.list_by_user(
            "user001"
        )
    ) == 1

    print("✅ User filtering")


    assert len(
        repository.list_security_events()
    ) == 1

    print("✅ Security event filtering")


    assert len(
        repository.list_failures()
    ) == 1

    print("✅ Failure filtering")


    assert len(
        repository.list_by_severity(
            AuditSeverity.ERROR
        )
    ) == 1

    print("✅ Severity filtering")


    start = datetime.now(UTC) - timedelta(
        minutes=1
    )

    end = datetime.now(UTC) + timedelta(
        minutes=1
    )


    assert len(
        repository.list_between(
            start,
            end,
        )
    ) == 2

    print("✅ Date filtering")


    assert repository.delete(
        "audit001"
    )

    assert repository.count() == 1

    print("✅ Delete")


    assert (
        repository.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health check")


    print(
        "\n🎉 AUDIT REPOSITORY TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()