from pathlib import Path


def test_disaster_recovery():

    print("\n================================")
    print("Disaster Recovery")
    print("================================\n")

    script = Path(
        "deployment/scripts/disaster_recovery.sh"
    )

    plan = Path(
        "deployment/disaster_recovery.md"
    )

    assert script.exists()

    assert plan.exists()

    script_text = script.read_text()

    assert "docker compose" in script_text

    assert "tar -xzf" in script_text

    assert "up -d" in script_text

    plan_text = plan.read_text()

    assert "RTO" in plan_text

    assert "RPO" in plan_text

    print("✅ Recovery script found")
    print("✅ Recovery plan documented")
    print("✅ Backup restoration configured")
    print("✅ Service recovery configured")
    print("✅ Recovery objectives documented")

    print("\n🎉 DISASTER RECOVERY PASSED\n")