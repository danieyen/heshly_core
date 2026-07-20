from heshly_core.services.security.account_lockout import (
    AccountLockout,
)
from heshly_core.services.security.brute_force_protection import (
    BruteForceProtection,
)
from heshly_core.services.security.ip_access_control import (
    IPAccessControl,
)
from heshly_core.services.security.security_alerts import (
    AlertLevel,
    SecurityAlerts,
)
from heshly_core.services.security.suspicious_activity_detection import (
    SuspiciousActivityDetection,
)


def run_test():

    print("\n================================")
    print("Threat Protection Test")
    print("================================\n")

    brute_force = BruteForceProtection()

    lockout = AccountLockout()

    detector = SuspiciousActivityDetection()

    ip_control = IPAccessControl()

    alerts = SecurityAlerts()

    print("✅ Services initialized")

    # =====================================================
    # Brute Force Protection
    # =====================================================

    username = "admin@example.com"

    ip = "192.168.1.10"

    for _ in range(5):

        brute_force.record_failure(
            username,
            ip,
        )

    assert brute_force.is_blocked(
        username,
        ip,
    )

    print("✅ Brute force protection")

    # =====================================================
    # Account Lockout
    # =====================================================

    lockout.lock(
        "user001"
    )

    assert lockout.is_locked(
        "user001"
    )

    print("✅ Account lockout")

    # =====================================================
    # Suspicious Activity
    # =====================================================

    detected = False

    for _ in range(5):

        detected = detector.record_event(

            activity_id="ACT001",

            tenant_id="tenant001",

            user_id="user001",

            ip_address=ip,

            activity_type="failed_login",

            description="Repeated failed logins",

        )

    assert detected

    print("✅ Suspicious activity detection")

    # =====================================================
    # IP Access
    # =====================================================

    ip_control.deny_ip(

        "10.0.0.100",

        "Known attacker",

    )

    assert not ip_control.is_allowed(
        "10.0.0.100"
    )

    print("✅ IP deny list")

    ip_control.allow_ip(

        "10.0.0.1",

        "Office",

    )

    assert ip_control.is_allowed(
        "10.0.0.1"
    )

    print("✅ IP allow list")

    # =====================================================
    # Alerts
    # =====================================================

    alert = alerts.create_alert(

        level=AlertLevel.CRITICAL,

        title="Threat detected",

        message="Repeated authentication failures",

        source="threat_protection",

        tenant_id="tenant001",

        user_id="user001",

    )

    assert alerts.count() == 1

    print("✅ Alert created")

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

    # =====================================================
    # Health
    # =====================================================

    assert (
        brute_force.health()["status"]
        ==
        "healthy"
    )

    assert (
        lockout.health()["status"]
        ==
        "healthy"
    )

    assert (
        detector.health()["status"]
        ==
        "healthy"
    )

    assert (
        ip_control.health()["status"]
        ==
        "healthy"
    )

    assert (
        alerts.health()["status"]
        ==
        "healthy"
    )

    print("✅ Health checks")

    print(
        "\n🎉 THREAT PROTECTION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()