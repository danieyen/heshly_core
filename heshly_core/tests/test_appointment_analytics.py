from datetime import UTC, datetime, timedelta

from heshly_core.models.appointment_analytics import (
    AnalyticsPeriod,
)
from heshly_core.services.analytics.appointment_analytics_manager import (
    AppointmentAnalyticsManager,
)


def build_sample_appointments():

    now = datetime.now(UTC)

    return [

        {
            "appointment_id": "APT-001",
            "business_id": "BIZ-001",
            "customer_name": "John Doe",
            "service_id": "SRV-001",
            "service_name": "Dental Cleaning",
            "employee_id": "EMP-001",
            "employee_name": "Dr. Alice",
            "room": "Room 1",
            "status": "completed",
            "amount": 4500,
            "duration": 60,
            "appointment_date": now - timedelta(days=5),
            "cancelled_at": None,
        },

        {
            "appointment_id": "APT-002",
            "business_id": "BIZ-001",
            "customer_name": "Mary Jane",
            "service_id": "SRV-002",
            "service_name": "Consultation",
            "employee_id": "EMP-002",
            "employee_name": "Dr. Bob",
            "room": "Room 2",
            "status": "cancelled",
            "reason": "Client Sick",
            "amount": 2500,
            "duration": 30,
            "appointment_date": now - timedelta(days=4),
            "cancelled_at": now - timedelta(days=5),
        },

        {
            "appointment_id": "APT-003",
            "business_id": "BIZ-001",
            "customer_name": "Peter Kim",
            "service_id": "SRV-001",
            "service_name": "Dental Cleaning",
            "employee_id": "EMP-001",
            "employee_name": "Dr. Alice",
            "room": "Room 1",
            "status": "completed",
            "amount": 4500,
            "duration": 60,
            "appointment_date": now - timedelta(days=3),
            "cancelled_at": None,
        },

        {
            "appointment_id": "APT-004",
            "business_id": "BIZ-001",
            "customer_name": "Lucy White",
            "service_id": "SRV-003",
            "service_name": "Root Canal",
            "employee_id": "EMP-003",
            "employee_name": "Dr. Carol",
            "room": "Room 3",
            "status": "no_show",
            "amount": 9000,
            "duration": 90,
            "appointment_date": now - timedelta(days=2),
            "cancelled_at": None,
        },

        {
            "appointment_id": "APT-005",
            "business_id": "BIZ-001",
            "customer_name": "James Bond",
            "service_id": "SRV-002",
            "service_name": "Consultation",
            "employee_id": "EMP-002",
            "employee_name": "Dr. Bob",
            "room": "Room 2",
            "status": "completed",
            "amount": 2500,
            "duration": 30,
            "appointment_date": now - timedelta(days=1),
            "cancelled_at": None,
        },

    ]


def build_history():

    today = datetime.now(UTC)

    history = []

    for i in range(30):

        history.append(

            {

                "date": today - timedelta(days=29 - i),

                "appointments": 18 + (i % 8),

            }

        )

    return history


def main():

    print("=" * 65)
    print(" HESHLY APPOINTMENT ANALYTICS FUNCTIONAL TEST")
    print("=" * 65)

    manager = AppointmentAnalyticsManager()

    appointments = build_sample_appointments()

    history = build_history()

    # =====================================================
    # Booking Analytics
    # =====================================================

    booking = manager.booking_report(

        "BIZ-001",

        appointments,

        AnalyticsPeriod.MONTHLY,

    )

    print("✓ Booking Analytics")

    # =====================================================
    # Cancellation Analytics
    # =====================================================

    cancellations = manager.cancellation_report(
        appointments
    )

    print("✓ Cancellation Analytics")

    # =====================================================
    # No-show Analytics
    # =====================================================

    no_shows = manager.no_show_report(
        appointments
    )

    print("✓ No-show Analytics")

    # =====================================================
    # Utilization
    # =====================================================

    utilization = manager.utilization_report(
        appointments
    )

    print("✓ Utilization Analytics")

    # =====================================================
    # Peak Hours
    # =====================================================

    peak = manager.peak_hours_report(
        appointments
    )

    print("✓ Peak Hours Analysis")

    # =====================================================
    # Forecasting
    # =====================================================

    forecast = manager.forecast(
        history,
        periods=7,
    )

    print("✓ Appointment Forecasting")

    # =====================================================
    # Complete Report
    # =====================================================

    report = manager.complete_report(

        "BIZ-001",

        appointments,

        history,

    )

    print("✓ Complete Analytics Report")

    # =====================================================
    # Health
    # =====================================================

    health = manager.health()

    assert health["status"] == "healthy"

    print("✓ Health Check")

    # =====================================================
    # Summary
    # =====================================================

    summary = manager.summary(report)

    print("\nAnalytics Summary")

    for key, value in summary.items():

        print(f"{key}: {value}")

    # =====================================================
    # Assertions
    # =====================================================

    assert booking.status_metrics.total == len(
        appointments
    )

    assert cancellations["cancelled"] == 1

    assert no_shows["no_shows"] == 1

    assert utilization["completed_appointments"] == 3

    assert len(
        forecast["forecast"]
    ) == 7

    assert summary["health"]["status"] == "healthy"

    print("\n" + "=" * 65)
    print("✅ APPOINTMENT ANALYTICS FUNCTIONAL TEST PASSED")
    print("=" * 65)


if __name__ == "__main__":
    main()