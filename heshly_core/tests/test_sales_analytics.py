from datetime import UTC, datetime, timedelta

from heshly_core.models.sales_analytics import (
    SalesAnalyticsPeriod,
)
from heshly_core.services.analytics.sales_analytics_manager import (
    SalesAnalyticsManager,
)


def sample_sales():

    now = datetime.now(UTC)

    return [

        {
            "sale_id": "SALE-001",
            "customer_id": "CUST-001",
            "customer_name": "John Doe",
            "employee_name": "Alice",
            "service_name": "Dental Cleaning",
            "amount": 5000,
            "discount": 500,
            "tax": 240,
            "total": 4740,
            "payment_method": "Cash",
            "status": "completed",
            "sale_date": now - timedelta(days=20),
        },

        {
            "sale_id": "SALE-002",
            "customer_id": "CUST-002",
            "customer_name": "Mary Jane",
            "employee_name": "Bob",
            "service_name": "Consultation",
            "amount": 3500,
            "discount": 0,
            "tax": 175,
            "total": 3675,
            "payment_method": "Card",
            "status": "completed",
            "sale_date": now - timedelta(days=15),
        },

        {
            "sale_id": "SALE-003",
            "customer_id": "CUST-003",
            "customer_name": "Peter Kim",
            "employee_name": "Alice",
            "service_name": "Root Canal",
            "amount": 15000,
            "discount": 1000,
            "tax": 700,
            "total": 14700,
            "payment_method": "M-Pesa",
            "status": "completed",
            "sale_date": now - timedelta(days=5),
        },

    ]


def sample_opportunities():

    now = datetime.now(UTC)

    return [

        {
            "opportunity_id": "OPP-001",
            "customer_name": "John Doe",
            "owner": "Alice",
            "source": "Website",
            "stage": "Proposal",
            "status": "won",
            "value": 5000,
            "probability": 100,
            "created_at": now - timedelta(days=15),
            "closed_at": now - timedelta(days=5),
        },

        {
            "opportunity_id": "OPP-002",
            "customer_name": "Mary Jane",
            "owner": "Bob",
            "source": "Referral",
            "stage": "Qualified",
            "status": "open",
            "value": 9000,
            "probability": 60,
            "created_at": now - timedelta(days=10),
            "closed_at": None,
        },

        {
            "opportunity_id": "OPP-003",
            "customer_name": "Peter Kim",
            "owner": "Alice",
            "source": "Website",
            "stage": "Proposal",
            "status": "lost",
            "value": 15000,
            "probability": 90,
            "loss_reason": "Price",
            "created_at": now - timedelta(days=25),
            "closed_at": now - timedelta(days=2),
        },

    ]


def revenue_history():

    now = datetime.now(UTC)

    return [

        {
            "date": now - timedelta(days=150),
            "revenue": 85000,
        },

        {
            "date": now - timedelta(days=120),
            "revenue": 91000,
        },

        {
            "date": now - timedelta(days=90),
            "revenue": 96000,
        },

        {
            "date": now - timedelta(days=60),
            "revenue": 102000,
        },

        {
            "date": now - timedelta(days=30),
            "revenue": 109000,
        },

    ]


def main():

    print("=" * 70)
    print(" HESHLY SALES ANALYTICS FUNCTIONAL TEST")
    print("=" * 70)

    manager = SalesAnalyticsManager()

    sales = sample_sales()
    opportunities = sample_opportunities()
    history = revenue_history()

    revenue = manager.revenue_report(sales)
    print("✓ Revenue Analytics")

    pipeline = manager.pipeline_report(opportunities)
    print("✓ Pipeline Analytics")

    conversion = manager.conversion_report(opportunities)
    print("✓ Conversion Analytics")

    win_loss = manager.win_loss_report(opportunities)
    print("✓ Win/Loss Analysis")

    forecast = manager.forecast_report(
        history,
        opportunities,
    )
    print("✓ Sales Forecasting")

    report = manager.complete_report(
        business_id="BIZ-001",
        sales=sales,
        opportunities=opportunities,
        history=history,
        period=SalesAnalyticsPeriod.MONTHLY,
    )
    print("✓ Complete Sales Analytics Report")

    health = manager.health()
    assert health["status"] == "healthy"
    print("✓ Health Check")

    summary = manager.summary(report)

    print("\nExecutive Summary")

    for key, value in summary.items():
        print(f"{key}: {value}")

    # --------------------------------------------------
    # Assertions
    # --------------------------------------------------

    assert revenue["total_sales"] == 3
    assert pipeline["total_opportunities"] == 3
    assert conversion["total_opportunities"] == 3
    assert win_loss["closed_opportunities"] == 2
    assert len(forecast["forecast"]) == 6

    assert report["business_id"] == "BIZ-001"
    assert summary["health"]["status"] == "healthy"

    print("\n" + "=" * 70)
    print("✅ SALES ANALYTICS FUNCTIONAL TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()