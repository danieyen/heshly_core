from heshly_core.services.analytics.dashboard_manager import (
    DashboardManager,
)


def main():

    print("=" * 60)
    print(" HESHLY BUSINESS DASHBOARD FUNCTIONAL TEST")
    print("=" * 60)

    manager = DashboardManager()

    # =====================================================
    # KPI Dashboard
    # =====================================================

    print("\nTesting KPI Dashboard...")

    kpi_dashboard = manager.build_kpi_dashboard(
        {
            "revenue": 850000,
            "appointments": 148,
            "customers": 92,
            "leads": 265,
            "conversion_rate": 41.5,
            "win_rate": 68.2,
            "opportunities": 37,
            "ai_accuracy": 96.8,
        }
    )

    assert kpi_dashboard.widget_count > 0

    print(
        f"✓ KPI Dashboard ({kpi_dashboard.widget_count} widgets)"
    )

    # =====================================================
    # Revenue Dashboard
    # =====================================================

    print("\nTesting Revenue Dashboard...")

    revenue_dashboard = manager.build_revenue_dashboard(
        {
            "total_revenue": 850000,
            "monthly_revenue": 125000,
            "average_sale": 17500,
            "target_percent": 82,
            "monthly_series": [
                80000,
                95000,
                105000,
                115000,
                125000,
            ],
            "service_breakdown": [
                ("Dental", 250000),
                ("Cleaning", 180000),
                ("Whitening", 95000),
            ],
            "customer_breakdown": [
                ("New", 55),
                ("Returning", 45),
            ],
        }
    )

    assert revenue_dashboard.widget_count > 0

    print(
        f"✓ Revenue Dashboard ({revenue_dashboard.widget_count} widgets)"
    )

    # =====================================================
    # Appointment Dashboard
    # =====================================================

    print("\nTesting Appointment Dashboard...")

    appointment_dashboard = manager.build_appointment_dashboard(
        {
            "total_appointments": 320,
            "today": 18,
            "completed": 280,
            "cancelled": 15,
            "no_shows": 12,
            "booking_rate": 88,
            "daily_trend": [15, 18, 22, 19, 24],
            "weekly_trend": [95, 101, 108, 115],
            "service_breakdown": [
                ("Consultation", 75),
                ("Cleaning", 120),
                ("Implants", 18),
            ],
            "staff_breakdown": [
                ("Dr A", 120),
                ("Dr B", 90),
                ("Dr C", 65),
            ],
        }
    )

    assert appointment_dashboard.widget_count > 0

    print(
        f"✓ Appointment Dashboard ({appointment_dashboard.widget_count} widgets)"
    )

    # =====================================================
    # CRM Dashboard
    # =====================================================

    print("\nTesting CRM Dashboard...")

    crm_dashboard = manager.build_crm_dashboard(
        {
            "total_leads": 520,
            "new_leads": 48,
            "qualified_leads": 210,
            "lead_conversion_rate": 42,
            "open_opportunities": 31,
            "won_opportunities": 18,
            "lost_opportunities": 6,
            "win_rate": 75,
            "pipeline_value": 1650000,
            "pipeline_stage_breakdown": [
                ("Qualified", 15),
                ("Proposal", 8),
                ("Negotiation", 5),
                ("Closed", 3),
            ],
            "followups_due": 12,
            "recent_activities": [
                ["Call", "John Doe"],
                ["Email", "Jane Doe"],
                ["WhatsApp", "Client A"],
            ],
            "lead_sources": [
                ("Google", 42),
                ("Facebook", 25),
                ("Referral", 18),
            ],
        }
    )

    assert crm_dashboard.widget_count > 0

    print(
        f"✓ CRM Dashboard ({crm_dashboard.widget_count} widgets)"
    )

    # =====================================================
    # Executive Dashboard
    # =====================================================

    print("\nTesting Executive Dashboard...")

    executive_dashboard = manager.build_executive_dashboard(
        {
            "revenue": 850000,
            "profit": 325000,
            "customers": 480,
            "appointments": 320,
            "leads": 520,
            "opportunities": 31,
            "pipeline_value": 1650000,
            "conversion_rate": 42,
            "customer_retention": 91,
            "ai_accuracy": 97,
            "business_health": 94,
            "monthly_revenue": [
                80000,
                90000,
                100000,
                110000,
                125000,
            ],
            "sales_trend": [
                30,
                45,
                55,
                60,
                72,
            ],
        }
    )

    assert executive_dashboard.widget_count > 0

    print(
        f"✓ Executive Dashboard ({executive_dashboard.widget_count} widgets)"
    )

    # =====================================================
    # Manager Statistics
    # =====================================================

    print("\nDashboard Statistics")

    stats = manager.statistics()

    print(stats)

    assert stats["total_dashboards"] == 5

    # =====================================================
    # Repository Tests
    # =====================================================

    print("\nTesting Dashboard Repository...")

    assert manager.exists("DASHBOARD-KPI")
    assert manager.exists("DASHBOARD-REVENUE")
    assert manager.exists("DASHBOARD-APPOINTMENTS")
    assert manager.exists("DASHBOARD-CRM")
    assert manager.exists("DASHBOARD-EXECUTIVE")

    print("✓ Dashboard Repository")

    # =====================================================
    # Health Check
    # =====================================================

    print("\nHealth Check")

    health = manager.health()

    print(health)

    assert health["status"] == "healthy"

    print("✓ Dashboard Manager Healthy")

    # =====================================================
    # Summary
    # =====================================================

    print("\nSummary")

    print(manager.summary())

    print("\n" + "=" * 60)
    print("✅ BUSINESS DASHBOARD FUNCTIONAL TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()