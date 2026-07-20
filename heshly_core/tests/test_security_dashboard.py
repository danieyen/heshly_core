from heshly_core.services.security.intrusion_detection import (
    IntrusionDetection,
)
from heshly_core.services.security.security_alerts import (
    AlertLevel,
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
    print("Security Dashboard Test")
    print("================================\n")

    metrics = SecurityMetrics()

    alerts = SecurityAlerts()

    intrusion = IntrusionDetection()

    dashboard = SecurityDashboard(

        metrics,

        alerts,

        intrusion,

    )

    print("✅ Dashboard initialized")

    # =====================================================
    # Metrics
    # =====================================================

    metrics.increment(
        "failed_logins",
        5,
    )

    metrics.increment(
        "blocked_ips",
        2,
    )

    print("✅ Metrics")

    # =====================================================
    # Alert
    # =====================================================

    alerts.create_alert(

        level=AlertLevel.CRITICAL,

        title="Brute Force",

        message="Multiple failed logins",

        source="authentication",

        tenant_id="tenant001",

    )

    print("✅ Alert")

    # =====================================================
    # Intrusion
    # =====================================================

    for _ in range(10):

        intrusion.record(

            event_id="IDS001",

            tenant_id="tenant001",

            user_id="user001",

            ip_address="192.168.1.15",

            event_type="failed_login",

            description="Repeated failures",

        )

    print("✅ Intrusion")

    # =====================================================
    # Dashboard
    # =====================================================

    summary = dashboard.summary()

    assert summary["metrics"]["failed_logins"] == 5

    assert summary["metrics"]["blocked_ips"] == 2

    assert summary["alerts"]["total"] == 1

    assert summary["intrusions"]["total"] == 1

    assert summary["overall_status"] == "critical"

    print("✅ Dashboard summary")

    assert (

        dashboard.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health")

    print(
        "\n🎉 SECURITY DASHBOARD TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()