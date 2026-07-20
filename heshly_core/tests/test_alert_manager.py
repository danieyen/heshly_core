from heshly_core.services.security.alert_manager import (
    AlertManager,
)
from heshly_core.services.security.security_alerts import (
    AlertLevel,
    SecurityAlerts,
)


def run_test():

    print("\n================================")
    print("Alert Manager Test")
    print("================================\n")

    alerts = SecurityAlerts()

    manager = AlertManager(
        alerts
    )

    print("✅ Manager initialized")

    alert = manager.warning(

        title="Failed Logins",

        message="Repeated failed login attempts",

        source="authentication",

        tenant_id="tenant001",

        user_id="user001",

    )

    print("✅ Alert created")

    assert alerts.count() == 1

    manager.escalate(
        alert.alert_id
    )

    assert (
        alerts.get(
            alert.alert_id
        ).level
        ==
        AlertLevel.HIGH
    )

    print("✅ Alert escalated")

    manager.acknowledge(
        alert.alert_id
    )

    assert alerts.get(
        alert.alert_id
    ).acknowledged

    print("✅ Alert acknowledged")

    manager.resolve(
        alert.alert_id
    )

    assert alerts.get(
        alert.alert_id
    ).resolved

    print("✅ Alert resolved")

    summary = manager.summary()

    assert summary["total"] == 1

    assert summary["critical"] == 0

    print("✅ Summary")

    assert (
        manager.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health")

    print(
        "\n🎉 ALERT MANAGER TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()