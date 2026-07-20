from datetime import UTC, datetime, timedelta

from heshly_core.models.analytics import (
    AnalyticsSnapshot,
    Dashboard,
    DashboardType,
)

from heshly_core.services.analytics.analytics_manager import (
    AnalyticsManager,
)


def main():

    print("=" * 60)
    print(" HESHLY ANALYTICS FOUNDATION FUNCTIONAL TEST")
    print("=" * 60)

    manager = AnalyticsManager()

    # =====================================================
    # Metrics Engine
    # =====================================================

    print("\nTesting Metrics Engine...")

    m1 = manager.metrics.count(
        "metric_001",
        "Total Leads",
        [1, 2, 3, 4, 5],
    )

    m2 = manager.metrics.total(
        "metric_002",
        "Revenue",
        [10000, 15000, 25000],
    )

    m3 = manager.metrics.average(
        "metric_003",
        "Average Deal",
        [10000, 20000, 30000],
    )

    m4 = manager.metrics.percentage(
        "metric_004",
        "Conversion Rate",
        45,
        100,
    )

    manager.save_metric(m1)
    manager.save_metric(m2)
    manager.save_metric(m3)
    manager.save_metric(m4)

    print("✓ Metrics Engine")

    # =====================================================
    # KPI Calculator
    # =====================================================

    print("Testing KPI Calculator...")

    k1 = manager.kpis.revenue_kpi(
        revenue=500000,
        target=450000,
    )

    k2 = manager.kpis.conversion_rate(
        converted=35,
        total=100,
    )

    k3 = manager.kpis.win_rate(
        won=18,
        total=30,
    )

    manager.save_kpi(k1)
    manager.save_kpi(k2)
    manager.save_kpi(k3)

    print("✓ KPI Calculator")

    # =====================================================
    # Time Series
    # =====================================================

    print("Testing Time Series Aggregation...")

    now = datetime.now(UTC)

    manager.time_series.add(now - timedelta(days=4), 10)
    manager.time_series.add(now - timedelta(days=3), 20)
    manager.time_series.add(now - timedelta(days=2), 30)
    manager.time_series.add(now - timedelta(days=1), 40)
    manager.time_series.add(now, 50)

    daily = manager.time_series.daily()
    monthly = manager.time_series.monthly()

    assert len(daily) == 5
    assert len(monthly) == 1

    print("✓ Time Series Aggregation")

    # =====================================================
    # Dashboard
    # =====================================================

    print("Testing Dashboard Repository...")

    dashboard = Dashboard(
        dashboard_id="dashboard_001",
        name="Executive Dashboard",
        dashboard_type=DashboardType.EXECUTIVE,
    )

    manager.save_dashboard(dashboard)

    assert manager.dashboard("dashboard_001") is not None

    print("✓ Dashboard Repository")

    # =====================================================
    # Snapshot
    # =====================================================

    print("Testing Snapshot Repository...")

    snapshot = AnalyticsSnapshot(
        snapshot_id="snapshot_001",
        business_id="BUS-001",
        period=k1.period,
    )

    snapshot.add_metric(m1)
    snapshot.add_metric(m2)

    snapshot.add_kpi(k1)
    snapshot.add_kpi(k2)

    manager.save_snapshot(snapshot)

    assert manager.snapshot("snapshot_001") is not None

    print("✓ Analytics Snapshot")

    # =====================================================
    # Filters
    # =====================================================

    print("Testing Data Filters...")

    records = [
        {
            "business_id": "BUS-001",
            "status": "Open",
            "value": 100,
            "created_at": now,
        },
        {
            "business_id": "BUS-002",
            "status": "Closed",
            "value": 500,
            "created_at": now,
        },
        {
            "business_id": "BUS-001",
            "status": "Open",
            "value": 300,
            "created_at": now,
        },
    ]

    filtered = manager.filters.by_business(
        records,
        "BUS-001",
    )

    assert len(filtered) == 2

    print("✓ Data Filters")

    # =====================================================
    # Repository Summary
    # =====================================================

    print("\nRepository Summary")

    print(manager.repository.summary())

    print("\nAnalytics Summary")

    print(manager.summary())

    # =====================================================
    # Assertions
    # =====================================================

    assert len(manager.metrics_list()) == 4
    assert len(manager.kpis_list()) == 3
    assert len(manager.dashboards()) == 1
    assert len(manager.snapshots()) == 1

    print("\n" + "=" * 60)
    print("✅ ANALYTICS FOUNDATION FUNCTIONAL TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()