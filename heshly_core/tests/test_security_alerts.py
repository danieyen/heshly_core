from heshly_core.services.security.security_alerts import (
    AlertLevel,
    SecurityAlerts,
)


def run_test():

    print("\n================================")
    print("Security Alerts Test")
    print("================================\n")

    alerts = SecurityAlerts()

    alert = alerts.create_alert(

        level=AlertLevel.CRITICAL,

        title="Brute Force Attack",

        message="Multiple failed login attempts detected.",

        source="authentication",

        tenant_id="tenant001",

        user_id="user001",

    )

    print("✅ Alert created")

    assert alerts.count() == 1

    print("✅ Alert stored")

    assert alerts.get(
        alert.alert_id
    ) is not None

    print("✅ Alert retrieved")

    assert len(
        alerts.list_by_level(
            AlertLevel.CRITICAL
        )
    ) == 1

    print("✅ Level filtering")

    alerts.acknowledge(
        alert.alert_id
    )

    assert alerts.get(
        alert.alert_id
    ).acknowledged

    print("✅ Alert acknowledged")

    alerts.resolve(
        alert.alert_id
    )

    assert alerts.get(
        alert.alert_id
    ).resolved

    print("✅ Alert resolved")

    assert len(
        alerts.list_unresolved()
    ) == 0

    print("✅ Unresolved filtering")

    assert (

        alerts.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 SECURITY ALERTS TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()