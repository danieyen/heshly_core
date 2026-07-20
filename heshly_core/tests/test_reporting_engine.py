from pathlib import Path

from heshly_core.models.reporting import (
    ReportFormat,
    ReportPeriod,
    ReportRequest,
    ReportType,
)
from heshly_core.services.reporting.report_manager import (
    ReportManager,
)


def sample_data():

    return {

        "summary": {

            "revenue": 850000,

            "appointments": 148,

            "customers": 61,

            "conversion_rate": 41.2,

        },

        "monthly_sales": [

            {
                "month": "January",
                "revenue": 245000,
            },

            {
                "month": "February",
                "revenue": 286000,
            },

            {
                "month": "March",
                "revenue": 319000,
            },

        ],

        "top_services": [

            {
                "service": "Dental Cleaning",
                "count": 82,
            },

            {
                "service": "Teeth Whitening",
                "count": 47,
            },

        ],

    }


def main():

    print("=" * 70)
    print("REPORTING ENGINE FUNCTIONAL TEST")
    print("=" * 70)

    manager = ReportManager()

    request = ReportRequest(

        report_id="RPT-001",

        business_id="BUS-001",

        report_type=ReportType.ANALYTICS,

        period=ReportPeriod.MONTH,

        output_format=ReportFormat.JSON,

        requested_by="System",

    )

    print("✓ Report Request Created")

    report = manager.build(
        request,
        sample_data(),
    )

    print("✓ Report Built")

    # --------------------------------------------------
    # JSON Export
    # --------------------------------------------------

    export = manager.export(
        report,
        ReportFormat.JSON,
    )

    print(
        f"✓ JSON Export: {export.filename}"
    )

    # --------------------------------------------------
    # PDF
    # --------------------------------------------------

    pdf = manager.export_pdf(
        report
    )

    print(
        f"✓ PDF Report: {pdf.name}"
    )

    # --------------------------------------------------
    # Excel
    # --------------------------------------------------

    excel = manager.export_excel(
        report
    )

    print(
        f"✓ Excel Report: {excel.name}"
    )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    summary = manager.summary(
        report
    )

    print("\nReport Summary")
    print("-" * 70)

    for key, value in summary.items():

        print(
            f"{key}: {value}"
        )

    # --------------------------------------------------
    # Health
    # --------------------------------------------------

    health = manager.health()

    print("\nHealth")
    print("-" * 70)

    for key, value in health.items():

        print(
            f"{key}: {value}"
        )

    # --------------------------------------------------
    # Assertions
    # --------------------------------------------------

    assert report.report_id == "RPT-001"

    assert report.rows > 0

    assert Path(
        export.download_url
    ).exists()

    assert pdf.exists()

    assert excel.exists()

    assert (
        health["status"]
        == "healthy"
    )

    print("\n" + "=" * 70)
    print("✅ REPORTING ENGINE FUNCTIONAL TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()