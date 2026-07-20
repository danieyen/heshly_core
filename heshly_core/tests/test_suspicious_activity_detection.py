from heshly_core.services.security.suspicious_activity_detection import (
    SuspiciousActivityDetection,
)


def run_test():

    print("\n================================")
    print("Suspicious Activity Detection Test")
    print("================================\n")

    detector = SuspiciousActivityDetection()

    detected = False

    for _ in range(5):

        detected = detector.record_event(

            activity_id="ACT001",

            tenant_id="tenant001",

            user_id="user001",

            ip_address="192.168.1.20",

            activity_type="failed_login",

            description="Repeated failed login",

        )

    assert detected

    print("✅ Suspicious activity detected")

    assert detector.count() == 1

    print("✅ Activity stored")

    activity = detector.get(
        "ACT001"
    )

    assert activity is not None

    print("✅ Activity retrieved")

    assert len(
        detector.unresolved()
    ) == 1

    print("✅ Unresolved query")

    detector.resolve(
        "ACT001"
    )

    assert len(
        detector.unresolved()
    ) == 0

    print("✅ Resolution")

    assert (

        detector.health()["status"]

        ==

        "healthy"

    )

    print("✅ Health check")

    print(
        "\n🎉 SUSPICIOUS ACTIVITY DETECTION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()