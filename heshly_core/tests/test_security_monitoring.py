from heshly_core.services.security.alert_manager import (
    AlertManager,
)
from heshly_core.services.security.incident_reporting import (
    IncidentReporting,
)
from heshly_core.services.security.intrusion_detection import (
    IntrusionDetection,
)
from heshly_core.services.security.security_alerts import (
    SecurityAlerts,
)
from heshly_core.services.security.security_dashboard import (
    SecurityDashboard,
)
from heshly_core.services.security.security_metrics import (
    SecurityMetrics,
)


def run_test():

    print("\n================================")
    print("Security Monitoring Test")
    print("================================\n")

    # =====================================================
    # Setup
    # =====================================================

    metrics = SecurityMetrics()

    alerts = SecurityAlerts()

    alert_manager = AlertManager(
        alerts
    )

    intrusion = IntrusionDetection()

    dashboard = SecurityDashboard(

        metrics,

        alerts,

        intrusion,

    )

    reporting = IncidentReporting(

        metrics,

        intrusion,

        alert_manager,

    )

    print("✅ Services initialized")

    # =====================================================
    # Metrics
    # =====================================================

    metrics.increment(
        "failed_logins",
        15,
    )

    metrics.increment(
        "blocked_ips",
        3,
    )

    metrics.increment(
        "security_alerts",
        1,
    )

    assert metrics.value(
        "failed_logins"
    ) == 15

    print("✅ Metrics")

    # =====================================================
    # Alerts
    # =====================================================

    alert = alert_manager.critical(

        title="Brute Force Attack",

        message="Multiple failed logins detected.",

        source="authentication",

        tenant_id="tenant001",

        user_id="user001",

    )

    assert alerts.count() == 1

    print("✅ Alerts")

    # =====================================================
    # Intrusion Detection
    # =====================================================

    detected = False

    for _ in range(10):

        detected = intrusion.record(

            event_id="IDS001",

            tenant_id="tenant001",

            user_id="user001",

            ip_address="192.168.1.25",

            event_type="failed_login",

            description="Repeated failed logins",

        )

    assert detected

    assert intrusion.count() == 1

    print("✅ Intrusion Detection")

    # =====================================================
    # Dashboard
    # =====================================================

    summary = dashboard.summary()

    assert summary["metrics"]["failed_logins"] == 15

    assert summary["alerts"]["total"] == 1

    assert summary["intrusions"]["total"] == 1

    assert summary["overall_status"] == "critical"

    print("✅ Dashboard")

    # =====================================================
    # Incident Report
    # =====================================================

    report = reporting.create_report(

        title="Authentication Attack",

        description="Detected brute-force activity.",

        severity="critical",

        tenant_id="tenant001",

    )

    assert reporting.count() == 1

    assert report.alerts == 1

    assert report.intrusions == 1

    assert len(
        report.recommendations
    ) > 0

    print("✅ Incident Reporting")

    # =====================================================
    # Alert Lifecycle
    # =====================================================

    alert_manager.acknowledge(
        alert.alert_id
    )

    alert_manager.resolve(
        alert.alert_id
    )

    assert alerts.get(
        alert.alert_id
    ).resolved

    print("✅ Alert Lifecycle")

    # =====================================================
    # Health
    # =====================================================

    assert metrics.health()["status"] == "healthy"

    assert intrusion.health()["status"] == "healthy"

    assert dashboard.health()["status"] == "healthy"

    assert alert_manager.health()["status"] == "healthy"

    assert reporting.health()["status"] == "healthy"

    print("✅ Health Checks")

    print(
        "\n🎉 SECURITY MONITORING TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()