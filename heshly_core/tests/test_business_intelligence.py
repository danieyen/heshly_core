from heshly_core.services.business_intelligence.bi_manager import (
    BIManager,
)


def main():

    print("=" * 70)
    print("BUSINESS INTELLIGENCE FUNCTIONAL TEST")
    print("=" * 70)

    manager = BIManager()

    revenue = [
        125000,
        138000,
        149000,
        162000,
        174000,
        181000,
    ]

    appointments = [
        52,
        58,
        60,
        69,
        71,
        75,
    ]

    customers = [
        31,
        37,
        42,
        47,
        54,
        61,
    ]

    print("\nTrend Analysis")
    print("-" * 70)

    trend = manager.trends.summary(
        revenue
    )

    print(trend)

    print("\nPredictive Analytics")
    print("-" * 70)

    forecast = manager.forecast(
        {
            "Revenue": revenue,
            "Appointments": appointments,
            "Customers": customers,
        },
        periods=3,
    )

    print(forecast)

    print("\nAnomaly Detection")
    print("-" * 70)

    anomaly = manager.anomalies.summary(
        revenue
    )

    print(anomaly)

    print("\nBenchmarking")
    print("-" * 70)

    benchmark = manager.benchmarking.summary(

        current_metrics={
            "Revenue": revenue[-1],
            "Appointments": appointments[-1],
        },

        benchmark_metrics={
            "Revenue": 175000,
            "Appointments": 80,
        },

    )

    print(benchmark)

    print("\nRecommendation Engine")
    print("-" * 70)

    recommendations = manager.recommendations.generate(

        trends=trend,

        anomalies=anomaly,

        benchmarks=benchmark,

    )

    for recommendation in recommendations:

        print(
            f"{recommendation.priority.upper()} : "
            f"{recommendation.title}"
        )

    print("\nComplete BI Analysis")
    print("-" * 70)

    analysis = manager.analyze(

        metric_name="Revenue",

        values=revenue,

        benchmark=175000,

    )

    print(analysis)

    print("\nBusiness Health")
    print("-" * 70)

    health = manager.business_health(

        {

            "Revenue": revenue,

            "Appointments": appointments,

            "Customers": customers,

        }

    )

    print(health)

    print("\nManager Health")
    print("-" * 70)

    manager_health = manager.health()

    print(manager_health)

    # -------------------------------------------------
    # Assertions
    # -------------------------------------------------

    assert trend["trend"] == "increasing"

    assert len(
        forecast["Revenue"]["forecast"]
    ) == 3

    assert "overall_health" in health

    assert (
        manager_health["status"]
        == "healthy"
    )

    assert (
        analysis["metric"]
        == "Revenue"
    )

    print("\n" + "=" * 70)
    print("✅ BUSINESS INTELLIGENCE TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()