from heshly_core.services.security.alert_manager import (
    AlertManager,
)
from heshly_core.services.security.incident_reporting import (
    IncidentReporting,
    IncidentStatus,
)
from heshly_core.services.security.intrusion_detection import (
    IntrusionDetection,
)
from heshly_core.services.security.security_alerts import (
    SecurityAlerts,
)
from heshly_core.services.security.security_metrics import (
    SecurityMetrics,
)


def run_test():

    print("\n================================")
    print("Incident Reporting Test")
    print("================================\n")

    metrics = SecurityMetrics()

    alerts = SecurityAlerts()

    manager = AlertManager(
        alerts
    )

    intrusion = IntrusionDetection()

    reporting = IncidentReporting(

        metrics,

        intrusion,

        manager,

    )

    print("✅ Services initialized")

    metrics.increment(
        "failed_logins",
        15,
    )

    manager.high(

        title="Brute Force",

        message="Multiple failed logins",

        source="authentication",

        tenant_id="tenant001",

    )

    for _ in range(10):

        intrusion.record(

            event_id="IDS001",

            tenant_id="tenant001",

            user_id="user001",

            ip_address="10.0.0.5",

            event_type="failed_login",

            description="Repeated failures",

        )

    report = reporting.create_report(

        title="Authentication Incident",

        description="Possible brute-force attack.",

        severity="high",

        tenant_id="tenant001",

    )

    print("✅ Report created")

    assert reporting.count() == 1

    assert report.alerts == 1

    assert report.intrusions == 1

    print("✅ Report contents")

    assert len(
        report.recommendations
    ) > 0

    print("✅ Recommendations")

    reporting.update_status(

        report.incident_id,

        IncidentStatus.RESOLVED,

    )

    assert (

        reporting.get(
            report.incident_id
        ).status

        ==

        IncidentStatus.RESOLVED

    )

    print("✅ Status updated")

    assert (

        reporting.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health")

    print(
        "\n🎉 INCIDENT REPORTING TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()