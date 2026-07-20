from heshly_core.services.monitoring.log_manager import (
    LogManager,
)


def test_log_management():

    print("\n================================")
    print("Log Management")
    print("================================\n")

    logs = LogManager()

    logs.info("Application started")
    logs.warning("High memory usage")
    logs.error("Database unavailable")

    assert logs.count() == 3

    entries = logs.entries()

    assert entries[0]["level"] == "INFO"
    assert entries[1]["level"] == "WARNING"
    assert entries[2]["level"] == "ERROR"

    logs.clear()

    assert logs.count() == 0

    print("✅ INFO logging")
    print("✅ WARNING logging")
    print("✅ ERROR logging")
    print("✅ Log storage")
    print("✅ Log cleanup")

    print("\n🎉 LOG MANAGEMENT PASSED\n")