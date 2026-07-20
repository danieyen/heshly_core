import time

from heshly_core.services.monitoring.performance_monitor import (
    PerformanceMonitor,
)


def test_performance_monitoring():

    print("\n================================")
    print("Performance Monitoring")
    print("================================\n")

    monitor = PerformanceMonitor()

    monitor.record_request(0.10)

    monitor.record_request(0.20)

    monitor.record_request(0.30)

    metrics = monitor.metrics()

    assert metrics["requests"] == 3

    assert metrics["last_response_time"] == 0.30

    assert metrics["average_response_time"] > 0

    assert monitor.uptime_seconds() >= 0

    health = monitor.health()

    assert health["status"] == "healthy"

    print("Requests :", metrics["requests"])

    print(
        "Average Response :",
        round(
            metrics["average_response_time"],
            3,
        ),
    )

    print(
        "Last Response :",
        metrics["last_response_time"],
    )

    print(
        "Uptime :",
        round(
            monitor.uptime_seconds(),
            2,
        ),
        "seconds",
    )

    print("\n🎉 PERFORMANCE MONITORING PASSED\n")