from datetime import UTC, datetime

from heshly_core.services.analytics.marketing_manager import (
    MarketingManager,
)


# ==========================================================
# Sample Data
# ==========================================================

def sample_leads():

    return [

        {
            "lead_id": "L001",
            "source": "Facebook",
            "status": "converted",
            "value": 15000,
            "cost": 1200,
            "customer": True,
            "appointment": True,
            "won": True,
        },

        {
            "lead_id": "L002",
            "source": "Google",
            "status": "converted",
            "value": 22000,
            "cost": 1800,
            "customer": True,
            "appointment": True,
            "won": True,
        },

        {
            "lead_id": "L003",
            "source": "Facebook",
            "status": "open",
            "value": 0,
            "cost": 650,
            "customer": False,
            "appointment": False,
            "won": False,
        },

        {
            "lead_id": "L004",
            "source": "WhatsApp",
            "status": "converted",
            "value": 12000,
            "cost": 300,
            "customer": True,
            "appointment": True,
            "won": True,
        },

    ]


def sample_campaigns():

    return [

        {
            "campaign_id": "CMP001",
            "campaign_name": "Facebook July",
            "channel": "Facebook",
            "impressions": 25000,
            "reach": 18000,
            "clicks": 940,
            "conversions": 82,
            "leads": 74,
            "appointments": 30,
            "customers": 18,
            "revenue": 240000,
            "spend": 52000,
        },

        {
            "campaign_id": "CMP002",
            "campaign_name": "Google Search",
            "channel": "Google",
            "impressions": 18000,
            "reach": 14500,
            "clicks": 730,
            "conversions": 66,
            "leads": 59,
            "appointments": 27,
            "customers": 15,
            "revenue": 215000,
            "spend": 47000,
        },

        {
            "campaign_id": "CMP003",
            "campaign_name": "WhatsApp Promo",
            "channel": "WhatsApp",
            "impressions": 9000,
            "reach": 8500,
            "clicks": 510,
            "conversions": 61,
            "leads": 53,
            "appointments": 28,
            "customers": 19,
            "revenue": 198000,
            "spend": 18000,
        },

    ]


def sample_conversions():

    return [

        {
            "customer_id": "C001",
            "conversion_value": 15000,
            "touchpoints": [
                "Facebook",
                "Google",
                "WhatsApp",
            ],
            "first_touch": "Facebook",
            "last_touch": "WhatsApp",
        },

        {
            "customer_id": "C002",
            "conversion_value": 22000,
            "touchpoints": [
                "Google",
                "WhatsApp",
            ],
            "first_touch": "Google",
            "last_touch": "WhatsApp",
        },

        {
            "customer_id": "C003",
            "conversion_value": 18000,
            "touchpoints": [
                "Facebook",
                "Website",
            ],
            "first_touch": "Facebook",
            "last_touch": "Website",
        },

    ]


# ==========================================================
# Functional Test
# ==========================================================

def main():

    print("=" * 70)
    print("MARKETING ANALYTICS FUNCTIONAL TEST")
    print("=" * 70)

    manager = MarketingManager()

    lead_report = manager.analyze_leads(
        sample_leads()
    )
    print("✓ Lead Source Analytics")

    channel_report = manager.analyze_channels(
        sample_campaigns()
    )
    print("✓ Channel Performance")

    roi_report = manager.analyze_roi(
        sample_campaigns()
    )
    print("✓ ROI Analytics")

    attribution_report = manager.analyze_attribution(
        sample_conversions()
    )
    print("✓ Campaign Attribution")

    dashboard = manager.dashboard_report(
        business_id="BIZ-001",
        leads=sample_leads(),
        campaigns=sample_campaigns(),
        conversions=sample_conversions(),
    )
    print("✓ Marketing Dashboard")

    report = manager.complete_report(
        business_id="BIZ-001",
        leads=sample_leads(),
        campaigns=sample_campaigns(),
        conversions=sample_conversions(),
    )
    print("✓ Marketing Manager")

    summary = manager.executive_summary(
        report
    )

    print("\nExecutive Summary")
    print("-" * 70)

    for key, value in summary.items():
        print(f"{key}: {value}")

    kpis = manager.kpis(report)

    print("\nKPI Snapshot")
    print("-" * 70)

    for key, value in kpis.items():
        print(f"{key}: {value}")

    # ------------------------------------------------------
    # Assertions
    # ------------------------------------------------------

    assert lead_report["total_sources"] >= 3
    assert channel_report["total_channels"] == 3
    assert roi_report["total_campaigns"] == 3
    assert attribution_report["total_conversions"] == 3

    assert dashboard["business_id"] == "BIZ-001"
    assert report["business_id"] == "BIZ-001"

    assert report["health"]["status"] == "healthy"

    print("\n" + "=" * 70)
    print("✅ MARKETING ANALYTICS FUNCTIONAL TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()