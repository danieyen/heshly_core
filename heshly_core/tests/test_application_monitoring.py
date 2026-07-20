from heshly_core.services.monitoring.application_monitor import (
    ApplicationMonitor,
)


def test_application_monitoring():

    print("\n================================")
    print("Application Monitoring")
    print("================================\n")

    monitor = ApplicationMonitor()

    health = monitor.health()

    metrics = monitor.metrics()

    assert health["status"] == "healthy"

    assert monitor.status() == "running"

    assert "cpu" in metrics

    assert "memory" in metrics

    assert "requests" in metrics

    assert "errors" in metrics

    print("Status   :", health["status"])
    print("Uptime   :", health["uptime"])
    print("Metrics  :", metrics)

    print("\n🎉 APPLICATION MONITORING PASSED\n")