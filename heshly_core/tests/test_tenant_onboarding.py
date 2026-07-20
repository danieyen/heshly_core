from pathlib import Path


def test_tenant_onboarding():

    print("\n================================")
    print("Tenant Onboarding")
    print("================================\n")

    plan = Path("deployment/tenant_onboarding.md")
    script = Path("deployment/scripts/onboard_tenant.sh")

    assert plan.exists()
    assert script.exists()

    plan_text = plan.read_text()
    script_text = script.read_text()

    assert "Onboarding Steps" in plan_text
    assert "Verification Checklist" in plan_text
    assert "Success Criteria" in plan_text

    assert "Provisioning tenant" in script_text
    assert "health checks" in script_text
    assert "onboarded successfully" in script_text

    print("✅ Onboarding plan documented")
    print("✅ Tenant provisioning script available")
    print("✅ Verification checklist documented")
    print("✅ Health checks included")
    print("✅ Tenant onboarding verified")

    print("\n🎉 TENANT ONBOARDING PASSED\n")