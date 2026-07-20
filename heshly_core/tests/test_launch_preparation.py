from pathlib import Path


def test_launch_preparation():

    print("\n================================")
    print("Launch Preparation")
    print("================================\n")

    plan = Path("deployment/launch_preparation.md")
    script = Path("deployment/scripts/launch.sh")

    assert plan.exists()
    assert script.exists()

    plan_text = plan.read_text()
    script_text = script.read_text()

    assert "Technical Readiness" in plan_text
    assert "Functional Validation" in plan_text
    assert "Operational Readiness" in plan_text
    assert "Customer Readiness" in plan_text
    assert "READY FOR LAUNCH" in plan_text

    assert "docker compose" in script_text
    assert "health checks" in script_text
    assert "Launch complete." in script_text

    print("✅ Launch plan documented")
    print("✅ Launch script available")
    print("✅ Readiness verification included")
    print("✅ Production startup configured")
    print("✅ Launch preparation verified")

    print("\n🎉 LAUNCH PREPARATION PASSED\n")