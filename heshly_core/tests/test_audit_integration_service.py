from heshly_core.services.integration.audit_integration import (
    AuditIntegration,
)



class FakeAuditService:

    def login(self, **kwargs):

        return {"id": "login001"}


    def logout(self, **kwargs):

        return {"id": "logout001"}


    def security_event(self, **kwargs):

        return {"id": "security001"}



class FakeTracker:

    def customer_created(
        self,
        tenant,
        user,
        reference,
    ):

        return {
            "id": "activity001"
        }



class FakeCompliance:

    def generate_report(
        self,
        tenant,
    ):

        return {
            "tenant": tenant,
            "events": 5,
        }



class FakeMetrics:

    def increment(
        self,
        key,
    ):

        pass



class FakeAlerts:

    def create(
        self,
        title,
        description,
    ):

        pass



def run_test():

    print("\n================================")
    print("Audit Integration Test")
    print("================================\n")


    integration = AuditIntegration(

        audit_service=FakeAuditService(),

        activity_tracker=FakeTracker(),

        compliance_reporting=FakeCompliance(),

        security_metrics=FakeMetrics(),

        security_alerts=FakeAlerts(),

    )


    print("✅ Services initialized")


    result = integration.record_login(
        "tenant001",
        "user001",
    )

    assert result.success

    print("✅ Login audit")


    result = integration.record_logout(
        "tenant001",
        "user001",
    )

    assert result.success

    print("✅ Logout audit")


    result = integration.track_activity(
        "customer_created",
        "tenant001",
        "user001",
        "CUST001",
    )

    assert result.success

    print("✅ Activity tracking")


    result = integration.record_security_event(
        "tenant001",
        "user001",
        "failed_login",
        "Multiple failures",
    )

    assert result.success

    print("✅ Security event")


    report = integration.compliance_report(
        "tenant001"
    )

    assert report["events"] == 5

    print("✅ Compliance report")


    assert (
        integration.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health")


    print(
        "\n🎉 AUDIT INTEGRATION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()