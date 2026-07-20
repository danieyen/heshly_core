from heshly_core.services.monitoring.error_tracker import (
    ErrorTracker,
)


def test_error_tracking():

    print("\n================================")
    print("Error Tracking")
    print("================================\n")

    tracker = ErrorTracker()

    try:
        raise ValueError("Sample error")

    except Exception as exc:
        tracker.capture(exc)

    assert tracker.count() == 1

    errors = tracker.errors()

    assert errors[0]["type"] == "ValueError"

    assert errors[0]["message"] == "Sample error"

    tracker.clear()

    assert tracker.count() == 0

    print("Tracked Errors :", errors)

    print("✅ Error capture")

    print("✅ Error storage")

    print("✅ Error cleanup")

    print("\n🎉 ERROR TRACKING PASSED\n")