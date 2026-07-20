from heshly_core.services.security.intrusion_detection import (
    IntrusionDetection,
    ThreatLevel,
)


def run_test():

    print("\n================================")
    print("Intrusion Detection Test")
    print("================================\n")

    detector = IntrusionDetection()

    detected = False

    for _ in range(10):

        detected = detector.record(

            event_id="IDS001",

            tenant_id="tenant001",

            user_id="user001",

            ip_address="192.168.1.15",

            event_type="failed_login",

            description="Repeated failed logins",

        )

    assert detected

    print("✅ Intrusion detected")

    assert detector.count() == 1

    print("✅ Event stored")

    event = detector.get(
        "IDS001"
    )

    assert event is not None

    assert (
        event.threat_level
        ==
        ThreatLevel.HIGH
    )

    print("✅ Threat level")

    assert len(
        detector.unresolved()
    ) == 1

    print("✅ Unresolved query")

    detector.resolve(
        "IDS001"
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
        "\n🎉 INTRUSION DETECTION TEST PASSED\n"
    )


if __name__ == "__main__":

    run_test()