from heshly_core.models.audit_log import (
    AuditEventType,
)
from heshly_core.repositories.audit_repository import (
    AuditRepository,
)
from heshly_core.services.security.audit_service import (
    AuditService,
)


def run_test():

    print("\n================================")
    print("Audit Service Test")
    print("================================\n")

    repository = AuditRepository()

    service = AuditService(
        repository
    )

    service.login(

        tenant_id="tenant001",

        user_id="user001",

    )

    print("✅ Login logged")

    service.logout(

        tenant_id="tenant001",

        user_id="user001",

    )

    print("✅ Logout logged")

    service.access_denied(

        tenant_id="tenant001",

        user_id="user001",

        resource="crm",

    )

    print("✅ Access denied logged")

    service.security_event(

        tenant_id="tenant001",

        user_id="user001",

        action="multiple_failed_logins",

        description="Five failed logins detected",

    )

    print("✅ Security event logged")

    service.log(

        tenant_id="tenant001",

        user_id="user001",

        event_type=AuditEventType.UPDATE,

        action="update_customer",

        resource="customer",

        description="Customer updated",

    )

    print("✅ Generic audit logged")

    assert len(
        service.history()
    ) == 5

    print("✅ History")

    assert len(
        service.tenant_history(
            "tenant001"
        )
    ) == 5

    print("✅ Tenant history")

    assert len(
        service.user_history(
            "user001"
        )
    ) == 5

    print("✅ User history")

    assert (

        service.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print("\n🎉 AUDIT SERVICE TEST PASSED\n")


if __name__ == "__main__":

    run_test()