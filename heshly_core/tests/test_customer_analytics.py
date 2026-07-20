from datetime import UTC, datetime, timedelta

from heshly_core.models.customer_analytics import (
    CustomerAnalyticsPeriod,
)
from heshly_core.services.analytics.customer_analytics_manager import (
    CustomerAnalyticsManager,
)


def sample_customers():

    now = datetime.now(UTC)

    return [

        {
            "customer_id": "CUST-001",
            "customer_name": "John Doe",
            "appointments": 10,
            "completed_appointments": 9,
            "cancelled_appointments": 1,
            "no_shows": 0,
            "total_spent": 75000,
            "first_visit": now - timedelta(days=365),
            "last_visit": now - timedelta(days=5),
            "visits": 10,
        },

        {
            "customer_id": "CUST-002",
            "customer_name": "Mary Jane",
            "appointments": 4,
            "completed_appointments": 3,
            "cancelled_appointments": 1,
            "no_shows": 0,
            "total_spent": 18000,
            "first_visit": now - timedelta(days=220),
            "last_visit": now - timedelta(days=70),
            "visits": 4,
        },

        {
            "customer_id": "CUST-003",
            "customer_name": "Peter Kim",
            "appointments": 2,
            "completed_appointments": 2,
            "cancelled_appointments": 0,
            "no_shows": 0,
            "total_spent": 6000,
            "first_visit": now - timedelta(days=120),
            "last_visit": now - timedelta(days=95),
            "visits": 2,
        },

        {
            "customer_id": "CUST-004",
            "customer_name": "Lucy White",
            "appointments": 1,
            "completed_appointments": 0,
            "cancelled_appointments": 0,
            "no_shows": 1,
            "total_spent": 0,
            "first_visit": now - timedelta(days=240),
            "last_visit": now - timedelta(days=210),
            "visits": 1,
        },

        {
            "customer_id": "CUST-005",
            "customer_name": "James Bond",
            "appointments": 7,
            "completed_appointments": 7,
            "cancelled_appointments": 0,
            "no_shows": 0,
            "total_spent": 42000,
            "first_visit": now - timedelta(days=400),
            "last_visit": now - timedelta(days=2),
            "visits": 7,
        },

    ]


def sample_feedback():

    return [

        {
            "customer_id": "CUST-001",
            "customer_name": "John Doe",
            "rating": 5,
            "nps": 10,
            "service_name": "Dental Cleaning",
            "employee_name": "Dr Alice",
            "sentiment": "positive",
        },

        {
            "customer_id": "CUST-002",
            "customer_name": "Mary Jane",
            "rating": 4,
            "nps": 8,
            "service_name": "Consultation",
            "employee_name": "Dr Bob",
            "sentiment": "positive",
        },

        {
            "customer_id": "CUST-003",
            "customer_name": "Peter Kim",
            "rating": 3,
            "nps": 6,
            "service_name": "Consultation",
            "employee_name": "Dr Bob",
            "sentiment": "neutral",
        },

        {
            "customer_id": "CUST-004",
            "customer_name": "Lucy White",
            "rating": 2,
            "nps": 2,
            "service_name": "Root Canal",
            "employee_name": "Dr Carol",
            "sentiment": "negative",
        },

        {
            "customer_id": "CUST-005",
            "customer_name": "James Bond",
            "rating": 5,
            "nps": 10,
            "service_name": "Dental Cleaning",
            "employee_name": "Dr Alice",
            "sentiment": "positive",
        },

    ]


def main():

    print("=" * 70)
    print(" HESHLY CUSTOMER ANALYTICS FUNCTIONAL TEST")
    print("=" * 70)

    manager = CustomerAnalyticsManager()

    customers = sample_customers()
    feedback = sample_feedback()

    # -----------------------------------------------------
    # Lifetime Value
    # -----------------------------------------------------

    clv = manager.lifetime_value(customers)

    print("✓ Customer Lifetime Value")

    # -----------------------------------------------------
    # Segmentation
    # -----------------------------------------------------

    segmentation = manager.segmentation_report(
        customers
    )

    print("✓ Customer Segmentation")

    # -----------------------------------------------------
    # Retention
    # -----------------------------------------------------

    retention = manager.retention_report(
        customers
    )

    print("✓ Retention Analytics")

    # -----------------------------------------------------
    # Churn
    # -----------------------------------------------------

    churn = manager.churn_report(
        customers
    )

    print("✓ Churn Prediction")

    # -----------------------------------------------------
    # Satisfaction
    # -----------------------------------------------------

    satisfaction = manager.satisfaction_report(
        feedback
    )

    print("✓ Customer Satisfaction")

    # -----------------------------------------------------
    # Complete Report
    # -----------------------------------------------------

    report = manager.complete_report(

        business_id="BIZ-001",

        customers=customers,

        feedback=feedback,

        period=CustomerAnalyticsPeriod.MONTHLY,

    )

    print("✓ Complete Customer Analytics Report")

    # -----------------------------------------------------
    # Health
    # -----------------------------------------------------

    health = manager.health()

    assert health["status"] == "healthy"

    print("✓ Health Check")

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    summary = manager.summary(report)

    print("\nExecutive Summary")

    for key, value in summary.items():

        print(f"{key}: {value}")

    # -----------------------------------------------------
    # Assertions
    # -----------------------------------------------------

    assert clv["total_customers"] == 5

    assert retention["total_customers"] == 5

    assert churn["total_customers"] == 5

    assert satisfaction["responses"] == 5

    assert report["business_id"] == "BIZ-001"

    assert summary["health"]["status"] == "healthy"

    print("\n" + "=" * 70)
    print("✅ CUSTOMER ANALYTICS FUNCTIONAL TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()