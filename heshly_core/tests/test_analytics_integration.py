from __future__ import annotations


# =====================================================
# Imports
# =====================================================

from heshly_core.api.analytics_api import (
    AnalyticsAPI,
)

from heshly_core.services.analytics.analytics_service import (
    AnalyticsService,
)

from heshly_core.services.analytics.analytics_manager import (
    AnalyticsManager,
)

from heshly_core.models.analytics import (
    Metric,
    MetricType,
    KPI,
    Dashboard,
    DashboardType,
    AnalyticsSnapshot,
    TimePeriod,
)


# =====================================================
# Final Integration Test
# =====================================================

def run_test():

    print("\n================================")
    print("Analytics Module Final Test")
    print("================================\n")


    # -------------------------------------------------
    # Initialize Layers
    # -------------------------------------------------

    print("Loading Analytics Manager...")

    manager = AnalyticsManager()

    assert manager is not None

    print("✅ Analytics Manager loaded")


    print("Loading Analytics Service...")

    service = AnalyticsService()

    assert service is not None

    print("✅ Analytics Service loaded")


    print("Loading Analytics API...")

    api = AnalyticsAPI()

    assert api is not None

    print("✅ Analytics API loaded")


    # -------------------------------------------------
    # Metric Storage
    # -------------------------------------------------

    print("\nTesting Metric storage...")


    metric = Metric(
        metric_id="test_metric",
        name="appointments_created",
        metric_type=MetricType.COUNT,
        value=100,
    )


    saved_metric = manager.save_metric(
        metric
    )


    assert saved_metric.metric_id == "test_metric"


    retrieved_metric = manager.metric(
        "test_metric"
    )


    assert retrieved_metric is not None

    assert retrieved_metric.value == 100


    print("✅ Metric storage passed")


    # -------------------------------------------------
    # KPI Storage
    # -------------------------------------------------

    print("\nTesting KPI storage...")


    kpi = KPI(
        kpi_id="test_kpi",
        name="conversion_rate",
        value=75,
        target=100,
    )


    saved_kpi = manager.save_kpi(
        kpi
    )


    assert saved_kpi.kpi_id == "test_kpi"


    retrieved_kpi = manager.kpi(
        "test_kpi"
    )


    assert retrieved_kpi is not None

    assert retrieved_kpi.value == 75


    print("✅ KPI storage passed")


    # -------------------------------------------------
    # Dashboard Storage
    # -------------------------------------------------

    print("\nTesting Dashboard storage...")


    dashboard = Dashboard(
        dashboard_id="test_dashboard",
        name="Executive Dashboard",
        dashboard_type=DashboardType.EXECUTIVE,
    )


    saved_dashboard = manager.save_dashboard(
        dashboard
    )


    assert saved_dashboard.dashboard_id == "test_dashboard"


    retrieved_dashboard = manager.dashboard(
        "test_dashboard"
    )


    assert retrieved_dashboard is not None


    print("✅ Dashboard storage passed")


    # -------------------------------------------------
    # Snapshot Storage
    # -------------------------------------------------

    print("\nTesting Snapshot storage...")


    snapshot = AnalyticsSnapshot(
        snapshot_id="test_snapshot",
        business_id="test_business",
        period=TimePeriod.MONTH,
    )


    saved_snapshot = manager.save_snapshot(
        snapshot
    )


    assert saved_snapshot.snapshot_id == "test_snapshot"


    retrieved_snapshot = manager.snapshot(
        "test_snapshot"
    )


    assert retrieved_snapshot is not None


    print("✅ Snapshot storage passed")


    # -------------------------------------------------
    # Analytics Service Layer
    # -------------------------------------------------

    print("\nTesting Service Layer...")


    overview = service.overview()


    assert overview is not None


    summary = service.summary()


    assert summary is not None


    report = service.report(
        "sales"
    )


    assert report is not None


    print("✅ Service Layer passed")


    # -------------------------------------------------
    # Analytics API Layer
    # -------------------------------------------------

    print("\nTesting API Layer...")


    assert api.analytics() is not None

    assert api.reporting() is not None

    assert api.business_intelligence() is not None


    print("✅ API Layer passed")


    # -------------------------------------------------
    # Health Checks
    # -------------------------------------------------

    print("\nTesting Health...")


    health = api.health()


    assert health is not None


    print("✅ Health check passed")


    # -------------------------------------------------
    # Summary
    # -------------------------------------------------

    print("\nTesting Summary...")


    summary = api.summary()


    assert summary is not None


    print("✅ Summary passed")


    # -------------------------------------------------
    # Cleanup
    # -------------------------------------------------

    manager.clear()


    print("\n================================")
    print("🎉 ANALYTICS MODULE FINAL TEST PASSED")
    print("================================\n")



if __name__ == "__main__":

    run_test()