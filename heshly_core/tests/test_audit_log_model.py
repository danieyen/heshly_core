from heshly_core.models.audit_log import (
    AuditEventType,
    AuditLog,
    AuditSeverity,
)


def run_test():

    print("\n================================")
    print("Audit Log Model Test")
    print("================================\n")


    audit = AuditLog(

        audit_id="audit001",

        tenant_id="tenant001",

        user_id="user001",

        event_type=AuditEventType.UPDATE,

        action="update_customer",

        resource="customer",

        description="Customer profile updated",

    )


    assert audit.event_type == (
        AuditEventType.UPDATE
    )

    print("✅ Event type stored")


    assert audit.severity == (
        AuditSeverity.INFO
    )

    print("✅ Default severity")


    security_event = AuditLog(

        audit_id="audit002",

        tenant_id="tenant001",

        user_id="user001",

        event_type=AuditEventType.SECURITY,

        action="failed_login",

        resource="authentication",

        severity=AuditSeverity.WARNING,

    )


    assert security_event.is_security_event

    print("✅ Security event detection")


    failed_event = AuditLog(

        audit_id="audit003",

        tenant_id="tenant001",

        user_id="user001",

        event_type=AuditEventType.ACCESS_DENIED,

        action="permission_denied",

        resource="api",

        severity=AuditSeverity.ERROR,

    )


    assert failed_event.is_failure

    print("✅ Failure detection")


    assert audit.created_at is not None

    print("✅ Timestamp generated")


    print(
        "\n🎉 AUDIT LOG MODEL TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()