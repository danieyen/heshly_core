from pathlib import Path


def test_go_live_validation():

    print("\n================================")
    print("Go-Live Validation")
    print("================================\n")

    report = Path("deployment/go_live_validation.md")
    script = Path("deployment/scripts/go_live_validation.sh")

    assert report.exists()
    assert script.exists()

    report_text = report.read_text()
    script_text = script.read_text()

    assert "Infrastructure Validation" in report_text
    assert "Application Validation" in report_text
    assert "Functional Validation" in report_text
    assert "Database Validation" in report_text
    assert "Monitoring Validation" in report_text
    assert "GO-LIVE SUCCESSFUL" in report_text

    assert "Checking production health" in script_text
    assert "Checking database" in script_text
    assert "Go-live validation completed successfully." in script_text

    print("✅ Infrastructure validated")
    print("✅ Application validated")
    print("✅ Functional services validated")
    print("✅ Database validated")
    print("✅ Monitoring validated")
    print("✅ Go-live validation completed")

    print("\n🎉 GO-LIVE VALIDATION PASSED\n")